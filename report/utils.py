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
    query = """SELECT 
                    pp.id, 
                    pp.default_code, 
                    pt.uom_id, 
                    pp.name_template || 
                    CASE 
                        WHEN STRING_AGG(pav.name, ', ' ORDER BY pav.id) IS NOT NULL THEN 
                            ' (' || STRING_AGG(pav.name, ', ' ORDER BY pav.id) || ')'
                        ELSE 
                            ''
                    END AS name_with_colors
                FROM product_product pp
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN product_template_company_allowed_rel ptc ON pt.id = ptc.template_id
                LEFT JOIN product_attribute_value_product_product_rel pav_rel ON pp.id = pav_rel.prod_id
                LEFT JOIN product_attribute_value pav ON pav.id = pav_rel.att_id
                WHERE (
                    (pt.company_id = 8 AND pt.categ_id IN (17273, 17350)) OR 
                    (ptc.company_id = 8)
                )
                GROUP BY pp.id, pp.name_template, pp.default_code, pt.uom_id;"""
    return execute_query(query)
