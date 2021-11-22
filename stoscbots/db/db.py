import mysql.connector
import pendulum
import enum
import logging
from dotenv import load_dotenv
import os


load_dotenv()

_user="stosc_ro"
_password=os.environ.get('STOSC_DB_PWD')
_host=os.environ.get('STOSC_DB_HOST')
_port=3306

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger=logging.getLogger(__name__)

class Databases(enum.Enum):
   CRM='stosc_churchcrm'
   FORMS='forms_db'

# Execute Query and return data
def __db_executeQuery(sql, db, prepared=False, *args):
    # Connect to MariaDB Platform
    try:
        conn=mysql.connector.connect( 
            user=_user, 
            password=_password, 
            host=_host, 
            port=_port, 
            database=db.value
        )
    except Exception as e:
        logger.error(e)
        raise
    try:
        if prepared:
            # Get Cursor 
            with conn.cursor(prepared=True) as cursor:
                cursor.execute(sql, args)
                _result=cursor.fetchall()            
        else:
            # Get Cursor 
            with conn.cursor() as cursor:
                cursor.execute(sql)
                _result=cursor.fetchall()
        return _result
    except Exception as e:
        logger.error(e)
    finally:
        # Close Connection
        conn.close()   

# ----------------------------------------------------------------------------------------------------------------------
def getNextServices():
    sql="select s.service_ID, s.service_Name, s.service_Date, s.attendees_Limit, sum(r.people_Count) as registered, s.group_ID from services s, registrations r where s.service_ID=r.service_ID and r.cancelled is null and s.service_Date > DATE_ADD(now(), INTERVAL -7 DAY) group by 1,2,3,4 order by s.service_Date, s.group_ID asc limit 8;"

    _result=__db_executeQuery(sql, Databases.FORMS)
    return _result
# ----------------------------------------------------------------------------------------------------------------------
def getBday(duration='w'):
    today=pendulum.now()
    if (duration.lower()) == "d":
        start=today.strftime("%Y%m%d")
        end=today.strftime("%Y%m%d")
    else:
        start=today.start_of('week').strftime("%Y%m%d")
        end=today.end_of('week').strftime("%Y%m%d")

    sql=f"SELECT left(right(fam_Name,5),4) as code, concat(IF(per_title IS NULL, '', per_title), ' ', per_firstname, ' ', per_lastname) AS NAME, concat_ws('/', `per_birthday`, `per_birthmonth`, `per_birthyear`) AS birthday, concat( year(CURRENT_DATE) - per_birthyear - 1, ' Yrs') AS 'Age'FROM `person_per`JOIN   `family_fam`ON family_fam.fam_id=person_per.per_fam_id where  `per_birthday` IS NOT null and `per_birthmonth` IS NOT null and per_cls_id <> 4 AND fam_datedeactivated IS null and person_per.per_cls_id != 4 and if(date_format({start}, '%m%d') > date_format({end}, '%m%d'), (date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN date_format({start}, '%m%d')AND'1231')OR(  date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN '0101'  AND  date_format({end}, '%m%d')), date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN date_format({start}, '%m%d')and date_format({end}, '%m%d') ) ORDER BY `per_birthmonth`, `per_birthday`"

    _result=__db_executeQuery(sql, Databases.CRM)
    return today.start_of('week').strftime("%b %d"), today.end_of('week').strftime("%b %d"), _result
# ----------------------------------------------------------------------------------------------------------------------
def getAnniversaries(duration='w'):
    today=pendulum.now()
    if (duration.lower()) == "d":
        start=today.strftime("%Y%m%d")
        end=today.strftime("%Y%m%d")
    else:
        start=today.start_of('week').strftime("%Y%m%d")
        end=today.end_of('week').strftime("%Y%m%d")

    sql=f"SELECT left(right(fam_Name,5),4) as code, concat(IF(hof.per_title IS NULL, '', hof.per_title), ' ', hof.per_firstname, ' ', hof.per_lastname, ' AND ', IF(spouse.per_title IS NULL, '', spouse.per_title), ' ', spouse.per_firstname, ' ', spouse.per_lastname) AS NAME, fam_weddingdate AS weddingdate FROM `family_fam`JOIN (SELECT * FROM `person_per` WHERE  per_fmr_id=1 AND per_id NOT IN ( SELECT r2p_record_id FROM   record2property_r2p WHERE  record2property_r2p.r2p_pro_id=12) AND per_cls_id <> 4) hof on fam_id=hof.per_fam_id join (SELECT * FROM   `person_per` WHERE  per_fmr_id=2 AND per_id NOT IN ( SELECT r2p_record_id FROM record2property_r2p WHERE  record2property_r2p.r2p_pro_id=12) AND    per_cls_id <> 4) spouse on fam_id=spouse.per_fam_id where  fam_datedeactivated IS null and if(date_format({start}, '%m%d') > date_format({end}, '%m%d'), (date_format(fam_weddingdate, '%m%d') BETWEEN date_format({start}, '%m%d')AND'1231')OR(date_format(fam_weddingdate, '%m%d') BETWEEN '0101'  AND  date_format({end}, '%m%d')), date_format(fam_weddingdate, '%m%d') BETWEEN date_format({start}, '%m%d')and date_format({end}, '%m%d') ) ORDER BY date_format(fam_weddingdate, '%m%d') ASC"

    _result=__db_executeQuery(sql, Databases.CRM)
    return today.start_of('week').strftime("%b %d"), today.end_of('week').strftime("%b %d"),_result
# ----------------------------------------------------------------------------------------------------------------------
def getMembersForArea(area_code):
    sql="select f.fam_Name from family_fam f, family_custom fc where f.fam_ID=fc.fam_ID and fc.c8=%s order by fam_Name"
    _result_members=__db_executeQuery(sql, Databases.CRM, True, area_code)

    sql="select lst_OptionName from list_lst where lst_ID = 30 and lst_OptionID=%s"
    _result_area_name=__db_executeQuery(sql, Databases.CRM, True, area_code)

    return _result_members,_result_area_name
# ----------------------------------------------------------------------------------------------------------------------
def get_member_details(search, search_type):
    if search_type == 'code':
        sql="select f.fam_ID, f.fam_Name, f.fam_Address1, f.fam_Address2, f.fam_Zip, f.fam_CellPhone, f.fam_HomePhone, f.fam_Email,IFNULL(fc.c1,'') as 'Home Parish', IFNULL(fc.c2,'') as 'Membership Date', IFNULL(fc.c4,'') as 'Related Families',IFNULL(fc.c5,FALSE) as 'Electoral Roll', IFNULL(l.lst_OptionName,'') as 'Prayer Group' from family_fam f inner join family_custom fc on f.fam_ID=fc.fam_ID and left(right(f.fam_Name,5),4)=%s and f.fam_DateDeactivated is null left join list_lst l on fc.c8=l.lst_OptionID and l.lst_ID =30"
        _result=__db_executeQuery(sql, Databases.CRM, True, search)
    elif search_type == 'free_text':
        search='%' + search + '%'
        sql="select CONCAT(per.per_FirstName,per.per_MiddleName,' ', per.per_LastName) as per_Name, f.fam_Name, per.per_Gender, CONCAT(`per_birthyear`) AS birth_year, per.per_fmr_ID from family_fam f inner JOIN person_per per on f.fam_ID = per.per_fam_ID and f.fam_DateDeactivated is null and (per.per_FirstName like %s or per.per_MiddleName like %s or per.per_LastName like %s) order by per_Name"
        _result=__db_executeQuery(sql, Databases.CRM, True, search, search, search)
    return _result
# ----------------------------------------------------------------------------------------------------------------------
def get_booking_GUID(memberCode):
    sql="select guid from family_fam where fam_Code= %s and enabled =1"
    _result=__db_executeQuery(sql, Databases.FORMS, True, memberCode)
    return _result
# ----------------------------------------------------------------------------------------------------------------------
def get_members_for_serviceID(service_ID):
    sql_next_service="select service_Name ,service_Date from services where service_ID =%s"
    _result1=__db_executeQuery(sql_next_service, Databases.FORMS,True,service_ID)

    sql=f"SELECT r.fam_code, f.fam_name, r .people_count, r.modified registered from registrations r inner JOIN services s on s.service_id=r.service_id inner JOIN family_fam f on f.fam_code=r.fam_code where r.cancelled IS null and r.service_id=%s ORDER BY r.modified ASC;"
    _result2=__db_executeQuery(sql, Databases.FORMS,True,service_ID)

    sql_count_of_kids = "SELECT count(1) from forms_db.registrations r inner JOIN forms_db.services s on s.service_id=r.service_id inner JOIN forms_db.family_fam f on f.fam_code=r.fam_code left OUTER join stosc_churchcrm.family_custom crm_family_custom on crm_family_custom.c7 = r.fam_code left OUTER JOIN stosc_churchcrm.family_fam crm_family_fam on crm_family_fam.fam_ID = crm_family_custom.fam_ID left outer JOIN stosc_churchcrm.person_per crm_person_per ON crm_person_per.per_fam_ID = crm_family_fam.fam_ID where r.cancelled IS null and r.service_id=%s AND DATE_ADD(CONCAT(crm_person_per.per_BirthYear,'-',crm_person_per.per_BirthMonth,'-',crm_person_per.per_BirthDay),INTERVAL(12) YEAR) > CURDATE() and crm_family_fam.fam_DateDeactivated is null"
    _result_count_kids=__db_executeQuery(sql_count_of_kids, Databases.FORMS,True,service_ID)

    return _result1[0][0], _result1[0][1].strftime("%a, %b %d %I:%M %p"), _result2, _result_count_kids