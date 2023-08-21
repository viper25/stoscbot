import os
import mysql.connector
import pendulum
import enum
import logging
import boto3
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv
from stoscbots.util.loggers import LOGLEVEL

# ----------------------------------------------------------------------------------------------------------------------
# Module logger
logger = logging.getLogger('DB')
logger.setLevel(LOGLEVEL)
# ----------------------------------------------------------------------------------------------------------------------

load_dotenv()

USER = "stosc_ro"
PASSWORD = os.environ.get('STOSC_DB_PWD')
HOST = os.environ.get('STOSC_DB_HOST')
PORT = 3306


class Databases(enum.Enum):
    CRM = 'stosc_churchcrm'
    FORMS = 'forms_db'


# Execute Query and return data
def __db_executeQuery(sql: str, db: enum, prepared=False, *args):
    # Connect to MariaDB Platform
    logger.debug(f"Query: [{sql}] on DB: [{db.value}]")
    try:
        conn = mysql.connector.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
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
                _result = cursor.fetchall()
        else:
            # Get Cursor 
            with conn.cursor() as cursor:
                cursor.execute(sql)
                _result = cursor.fetchall()
        return _result
    except Exception as e:
        logger.error(e)
    finally:
        # Close Connection
        conn.close()
    # ----------------------------------------------------------------------------------------------------------------------


def get_bday(duration: str = 'w'):
    today = pendulum.now()
    if (duration.lower()) == "d":
        start = today.strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")
    else:
        start = today.start_of('week').strftime("%Y%m%d")
        end = today.end_of('week').strftime("%Y%m%d")

    sql = f"SELECT left(right(fam_Name,5),4) as code, concat(per_firstname, ' ', per_lastname) AS NAME, concat_ws('/', `per_birthday`, `per_birthmonth`, `per_birthyear`) AS birthday, concat( year(CURRENT_DATE) - per_birthyear - 1, ' Yrs') AS 'Age'FROM `person_per`JOIN   `family_fam`ON family_fam.fam_id=person_per.per_fam_id where  `per_birthday` IS NOT null and `per_birthmonth` IS NOT null and per_cls_id <> 4 AND fam_datedeactivated IS null and person_per.per_cls_id != 4 and if(date_format({start}, '%m%d') > date_format({end}, '%m%d'), (date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN date_format({start}, '%m%d')AND'1231')OR(  date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN '0101'  AND  date_format({end}, '%m%d')), date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN date_format({start}, '%m%d')and date_format({end}, '%m%d') ) ORDER BY `per_birthmonth`, `per_birthday`"

    _result = __db_executeQuery(sql, Databases.CRM)
    return today.start_of('week').strftime("%b %d"), today.end_of('week').strftime("%b %d"), _result


# ----------------------------------------------------------------------------------------------------------------------
def get_anniversaries(duration: str = 'w'):
    today = pendulum.now()
    if (duration.lower()) == "d":
        start = today.strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")
    else:
        start = today.start_of('week').strftime("%Y%m%d")
        end = today.end_of('week').strftime("%Y%m%d")

    sql = f"SELECT left(right(fam_Name,5),4) as code, concat(hof.per_firstname, ' ', hof.per_lastname, ' & ', spouse.per_firstname, ' ', spouse.per_lastname) AS NAME, fam_weddingdate AS weddingdate FROM `family_fam`JOIN (SELECT * FROM `person_per` WHERE  per_fmr_id=1 AND per_id NOT IN ( SELECT r2p_record_id FROM   record2property_r2p WHERE  record2property_r2p.r2p_pro_id=12) AND per_cls_id <> 4) hof on fam_id=hof.per_fam_id join (SELECT * FROM   `person_per` WHERE  per_fmr_id=2 AND per_id NOT IN ( SELECT r2p_record_id FROM record2property_r2p WHERE  record2property_r2p.r2p_pro_id=12) AND    per_cls_id <> 4) spouse on fam_id=spouse.per_fam_id where  fam_datedeactivated IS null and if(date_format({start}, '%m%d') > date_format({end}, '%m%d'), (date_format(fam_weddingdate, '%m%d') BETWEEN date_format({start}, '%m%d')AND'1231')OR(date_format(fam_weddingdate, '%m%d') BETWEEN '0101'  AND  date_format({end}, '%m%d')), date_format(fam_weddingdate, '%m%d') BETWEEN date_format({start}, '%m%d')and date_format({end}, '%m%d') ) ORDER BY date_format(fam_weddingdate, '%m%d') ASC"

    _result = __db_executeQuery(sql, Databases.CRM)
    return today.start_of('week').strftime("%b %d"), today.end_of('week').strftime("%b %d"), _result


# ----------------------------------------------------------------------------------------------------------------------
def get_members_for_area(area_code: str):
    sql = "select f.fam_Name from family_fam f, family_custom fc where f.fam_ID=fc.fam_ID and f.fam_DateDeactivated is null and fc.c8=%s order by fam_Name"
    _result_members = __db_executeQuery(sql, Databases.CRM, True, area_code)

    sql = "select lst_OptionName from list_lst where lst_ID = 30 and lst_OptionID=%s"
    _result_area_name = __db_executeQuery(sql, Databases.CRM, True, area_code)

    return _result_members, _result_area_name


# ----------------------------------------------------------------------------------------------------------------------
def get_member_details(search: str, search_type: str):
    if search_type == 'code':
        sql = "select f.fam_ID, SUBSTRING(f.fam_Name, POSITION('(' IN f.fam_Name) + 1, 4) as fam_Code, LEFT(f.fam_Name, char_length(f.fam_Name) -7) as fam_Name, f.fam_Email, tbl_husband.Husband, tbl_husband.Husband_Email, tbl_wife.Wife, tbl_wife.Wife_Email, tbl_children.Children, tbl_others.Others, f.fam_Address1, f.fam_Address2, f.fam_Zip, f.fam_CellPhone, f.fam_HomePhone, IFNULL(fc.c1, '') as 'Home Parish', IFNULL(fc.c2, '') as 'Membership Date', IFNULL(fc.c4, '') as 'Related Families', IFNULL(fc.c5, FALSE) as 'Electoral Roll', IFNULL(l.lst_OptionName, '') as 'Prayer Group', Husband_DOB, Wife_DOB, pp.per_Gender, pp.per_fmr_ID from family_fam f inner join family_custom fc on f.fam_ID = fc.fam_ID and SUBSTRING(f.fam_Name, POSITION('(' IN f.fam_Name) + 1, 4) = %s and f.fam_DateDeactivated is null INNER join person_per pp on f.fam_ID = pp.per_fam_ID /*  Remove deceased  */ and pp.per_cls_ID != 4 left join list_lst l on fc.c8 = l.lst_OptionID /*  Area Prayer Group List  */ and l.lst_ID = 30 left OUTER JOIN ( select per_fam_id, group_concat( pp.per_FirstName, ' ', if(pp.per_LastName != '', pp.per_LastName, '') ORDER BY pp.per_BirthYear) as Children from person_per pp where per_fmr_ID = 3 GROUP BY per_fam_id order by per_fam_ID ) as tbl_children ON tbl_children.per_fam_ID = f.fam_ID left OUTER JOIN ( select per_fam_id, per_Email as Husband_Email, group_concat( pp.per_FirstName, ' ', if(pp.per_LastName != '', pp.per_LastName, '')) as Husband, CONCAT( per_BirthYear, '-', LPAD(per_BirthMonth, 2, '0'), '-', LPAD(per_BirthDay, 2, '0') ) as Husband_DOB from person_per pp where per_Gender  = 1 and per_fmr_ID in (1,2) GROUP BY per_fam_id order by per_fam_ID ) as tbl_husband ON tbl_husband.per_fam_ID = f.fam_ID left OUTER JOIN ( select per_fam_id, per_Email as Wife_Email, group_concat( pp.per_FirstName, ' ', if(pp.per_LastName != '', pp.per_LastName, '') ) as Wife, CONCAT( per_BirthYear, '-', LPAD(per_BirthMonth, 2, '0'), '-', LPAD(per_BirthDay, 2, '0') ) as Wife_DOB from person_per pp where per_Gender = 2 and per_fmr_ID in (1,2) GROUP BY per_fam_id order by per_fam_ID ) as tbl_wife ON tbl_wife.per_fam_ID = f.fam_ID left OUTER JOIN ( select per_fam_id, group_concat( pp.per_FirstName, ' ', if(pp.per_LastName != '', pp.per_LastName, '') ) as Others from person_per pp where per_fmr_ID = 7 GROUP BY per_fam_id order by per_fam_ID ) as tbl_others ON tbl_others.per_fam_ID = f.fam_ID GROUP by fam_Code order by fam_Code"
        _result = __db_executeQuery(sql, Databases.CRM, True, search)
    elif search_type == 'free_text':
        search = '%' + search + '%'
        sql = "select f.fam_ID, SUBSTRING(f.fam_Name, POSITION('(' IN f.fam_Name) + 1, 4) as fam_Code, LEFT(f.fam_Name, char_length(f.fam_Name) -7) as fam_Name, f.fam_Email, tbl_husband.Husband, tbl_husband.Husband_Email, tbl_wife.Wife, tbl_wife.Wife_Email, tbl_children.Children, tbl_others.Others, f.fam_Address1, f.fam_Address2, f.fam_Zip, f.fam_CellPhone, f.fam_HomePhone, IFNULL(fc.c1, '') as 'Home Parish', IFNULL(fc.c2, '') as 'Membership Date', IFNULL(fc.c4, '') as 'Related Families', IFNULL(fc.c5, FALSE) as 'Electoral Roll', IFNULL(l.lst_OptionName, '') as 'Prayer Group', Husband_DOB, Wife_DOB, pp.per_Gender, pp.per_fmr_ID, CONCAT(pp.per_FirstName,' ',pp.per_MiddleName,pp.per_LastName) as search_person, pp.per_ID from family_fam f inner join family_custom fc on f.fam_ID = fc.fam_ID and f.fam_DateDeactivated is null INNER join person_per pp on f.fam_ID = pp.per_fam_ID /*  Remove deceased  */ and pp.per_cls_ID != 4 and (pp.per_FirstName like %s or pp.per_MiddleName like %s or pp.per_LastName like %s) left join list_lst l on fc.c8 = l.lst_OptionID /*  Area Prayer Group List  */ and l.lst_ID = 30 left OUTER JOIN ( select per_fam_id, group_concat( pp.per_FirstName, ' ', if(pp.per_LastName != '', pp.per_LastName, '') ORDER BY pp.per_BirthYear) as Children from person_per pp where per_fmr_ID = 3 GROUP BY per_fam_id order by per_fam_ID ) as tbl_children ON tbl_children.per_fam_ID = f.fam_ID left OUTER JOIN ( select per_fam_id, per_Email as Husband_Email, group_concat( pp.per_FirstName, ' ', if(pp.per_LastName != '', pp.per_LastName, '') ) as Husband, CONCAT( per_BirthYear, '-', LPAD(per_BirthMonth, 2, '0'), '-', LPAD(per_BirthDay, 2, '0') ) as Husband_DOB from person_per pp where per_Gender = 1 and per_fmr_ID in (1,2) GROUP BY per_fam_id order by per_fam_ID ) as tbl_husband ON tbl_husband.per_fam_ID = f.fam_ID left OUTER JOIN ( select per_fam_id, per_Email as Wife_Email, group_concat( pp.per_FirstName, ' ', if(pp.per_LastName != '', pp.per_LastName, '') ) as Wife, CONCAT( per_BirthYear, '-', LPAD(per_BirthMonth, 2, '0'), '-', LPAD(per_BirthDay, 2, '0') ) as Wife_DOB from person_per pp where per_Gender = 2 and per_fmr_ID in (1,2) GROUP BY per_fam_id order by per_fam_ID ) as tbl_wife ON tbl_wife.per_fam_ID = f.fam_ID left OUTER JOIN ( select per_fam_id, group_concat( pp.per_FirstName, ' ', if(pp.per_LastName != '', pp.per_LastName, '') ) as Others from person_per pp where per_fmr_ID = 7 GROUP BY per_fam_id order by per_fam_ID ) as tbl_others ON tbl_others.per_fam_ID = f.fam_ID GROUP by fam_Code order by fam_Code"
        _result = __db_executeQuery(sql, Databases.CRM, True, search, search, search)
    return _result


# ----------------------------------------------------------------------------------------------------------------------
def get_person_name(person_ID: str):
    sql = "select CONCAT(per_FirstName,' ',per_MiddleName,per_LastName) as person from person_per where per_ID = %s"
    return __db_executeQuery(sql, Databases.CRM, True, person_ID)


# ----------------------------------------------------------------------------------------------------------------------
def get_members_born_on(year: str):
    sql = "select CONCAT(crm_person_per.per_FirstName,' ', crm_person_per.per_MiddleName,' ', crm_person_per.per_LastName), CONCAT(crm_person_per.per_BirthYear,'-',LPAD(crm_person_per.per_BirthMonth,2,'0'),'-',LPAD(crm_person_per.per_BirthDay,2,'0')), fam.fam_Name ,fam.fam_Email, fam.fam_HomePhone, fam.fam_CellPhone from stosc_churchcrm.person_per crm_person_per inner join family_fam fam on crm_person_per.per_fam_ID = fam.fam_ID where fam.fam_DateDeactivated is null and crm_person_per.per_BirthYear = %s order by CONCAT(crm_person_per.per_BirthYear,LPAD(crm_person_per.per_BirthMonth,2,'0'),LPAD(crm_person_per.per_BirthDay,2,'0'))"
    return __db_executeQuery(sql, Databases.CRM, True, year)


# ----------------------------------------------------------------------------------------------------------------------
def get_gb_eligible_count():
    sql = "SELECT count(1) FROM `person_per`  INNER JOIN `family_fam` ON family_fam.fam_ID = person_per.per_fam_ID INNER JOIN `family_custom` ON family_custom.fam_ID = person_per.per_fam_ID WHERE person_per.per_fmr_ID in (1,2) AND person_per.per_cls_ID <> 4 AND person_per.per_id not in (select r2p_record_id from record2property_r2p where record2property_r2p.r2p_pro_ID = 12) AND family_custom.c5 = 'TRUE' AND family_fam.fam_DateDeactivated is null ORDER BY family_custom.c7"
    return __db_executeQuery(sql, Databases.CRM, True)


# ----------------------------------------------------------------------------------------------------------------------
def add_user(telegram_id, member_code, name):
    # Insert into DynamoDB table
    resource = boto3.resource(
        "dynamodb",
        aws_access_key_id=os.environ.get("STOSC_DDB_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("STOSC_DDB_SECRET_ACCESS_KEY"),
        region_name="ap-southeast-1",
    )
    table = resource.Table('stosc_bot_member_telegram')

    # First check if this user exists in DynamoDB
    response = table.query(KeyConditionExpression=Key("telegram_id").eq(telegram_id))

    if len(response['Items']) == 0:
        # User does not exist, create a new record
        chunk = {
            'telegram_id': telegram_id,
            'member_code': member_code,
            'Name': name,
            'hits': 0,
        }
        result = table.put_item(Item=chunk)
        return result['ResponseMetadata']['HTTPStatusCode']
    elif len(response['Items']) > 0:
        # Use exists, 500 indicating existing user
        return 500
