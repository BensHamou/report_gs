from account.models import Setting
import psycopg2

def connect_database():
    port = Setting.objects.get(name='port').value
    host = Setting.objects.get(name='host').value
    dbname = Setting.objects.get(name='dbname').value
    user = Setting.objects.get(name='user').value
    password = Setting.objects.get(name='password').value
    conn_string = ("host="+host+" port="+port+" dbname="+dbname+" user="+user+" password="+password)
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    return cursor

def execute_query(query, params=None):
    with connect_database() as cursor:
        cursor.execute(query, params)
        records = cursor.fetchall()
    return records


def getMProducts():
    query = """SELECT pp.id, pp.name_template, pp.default_code, pt.uom_id 
                FROM product_product pp
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                LEFT JOIN product_template_company_allowed_rel ptc on pt.id = ptc.template_id
                WHERE (pt.company_id = 8 OR ptc.company_id = 8) and pt.categ_id in (17273, 17350);"""
    return execute_query(query)
