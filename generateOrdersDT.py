import numpy as np
import os, time, random
from datetime import timedelta
from rockset import Client, Q, F
from rockset.exception import InputError


workspace = 'retail'
targetCollName = 'recent_orders_dt'
retentionSec = 10 * 60

# tl = Timeloop()


def dropTargetColl(rs):
    try: 
        coll = rs.retrieve(targetCollName, workspace = workspace)
        coll.drop()
        time.sleep(10)
    except InputError:
        # collection doesn't exist. Need more checking here.
        return
    except:
        raise

def createTargetColl(rs):


    try: 
        coll = rs.retrieve(targetCollName, workspace = workspace)
        # collection exists
        return coll
    except InputError:
        # collection doesn't exist. Need more checking here.
        print("Target collection does not exist")

    field_mappings = [
        rs.FieldMapping.mapping(
            name="purchased",
            input_fields=[
                rs.FieldMapping.input_field(
                field_name = "purchased",
                if_missing = "PASS",
                is_drop = True,
                param = "purchased_str"
                )
            ],
            output_field=rs.FieldMapping.output_field(
                field_name = "purhcased",
                sql_expression = "TRY_CAST(:purchased_str AS datetime)",
                on_error="SKIP"
                )
            ),
        rs.FieldMapping.mapping(
            name="approved",
            input_fields=[
                rs.FieldMapping.input_field(
                field_name = "approved",
                if_missing = "PASS",
                is_drop = True,
                param = "approved_str"
                )
            ],
            output_field=rs.FieldMapping.output_field(
                field_name = "approved",
                sql_expression = "TRY_CAST(:approved_str AS datetime)",
                on_error="SKIP"
                )
            ),
        rs.FieldMapping.mapping(
            name="delivered_carrier",
            input_fields=[
                rs.FieldMapping.input_field(
                field_name = "delivered_carrier",
                if_missing = "PASS",
                is_drop = True,
                param = "delivered_carrier_str"
                )
            ],
            output_field=rs.FieldMapping.output_field(
                field_name = "delivered_carrier",
                sql_expression = "TRY_CAST(:delivered_carrier_str AS datetime)",
                on_error="SKIP"
                )
            ),
        rs.FieldMapping.mapping(
            name="delivered_customer",
            input_fields=[
                rs.FieldMapping.input_field(
                field_name = "delivered_customer",
                if_missing = "PASS",
                is_drop = True,
                param = "delivered_customer_str"
                )
            ],
            output_field=rs.FieldMapping.output_field(
                field_name = "delivered_customer",
                sql_expression = "TRY_CAST(:delivered_customer_str AS datetime)",
                on_error="SKIP"
                )
            ),
        rs.FieldMapping.mapping(
            name="estimated_delivery",
            input_fields=[
                rs.FieldMapping.input_field(
                field_name = "estimated_delivery",
                if_missing = "PASS",
                is_drop = True,
                param = "estimated_delivery_str"
                )
            ],
            output_field=rs.FieldMapping.output_field(
                field_name = "estimated_delivery",
                sql_expression = "TRY_CAST(:estimated_delivery_str AS datetime)",
                on_error="SKIP"
                )
            )
        ]

    attempt = 0
    delay = 1

    while attempt < 8:
        try:
            targetColl = rs.Collection.create(targetCollName, workspace = workspace, field_mappings = field_mappings,  retention_secs = retentionSec)
            return targetColl
        except InputError:
            sleep = (delay * 2 ** attempt + random.uniform(0,1))
            print("Waiting for target collection to be deleted: " + str(sleep))
            time.sleep(sleep)
            attempt += 1
        except:
            raise

def confirmTargetReady(coll):
    attempt = 0
    delay = 1
    while attempt < 8:
        try:
            description = coll.describe()
            if description.data.status == "READY" :
                return
            sleep = (delay * 2 ** attempt + random.uniform(0,1))
            print("Waiting for target collection to be ready: " + str(sleep))
            time.sleep(sleep)
            attempt += 1
        except:
            raise

def getSourceDocs(rs, limit):
    q = Q('retail.orders_1').lowest(limit, F["_event_time"])
    return rs.sql(q)

def processOrders(rs, targetColl, sourceDocs, avgDelay):
    # target = rs.Collection.retrieve('recentOrders', workspace= 'retail')
    for doc in sourceDocs:
        print(doc['_id'])
        output = dict(doc.items())
        del output['_event_time']
        targetColl.add_docs([output])
        # target.add_docs([doc])
        time.sleep(random.uniform(avgDelay * 0.5 ,avgDelay * 2))

def main():
    key = os.getenv('ROCKSET_API_KEY')
    rs = Client(api_key = key,
      api_server='https://api.rs2.usw2.rockset.com')
    try:
        # dropTargetColl(rs)
        targetColl = createTargetColl(rs)
        confirmTargetReady(targetColl)
        sourceDocs = getSourceDocs(rs, 99000)
        processOrders(rs, targetColl, sourceDocs, 0.5)
        print("Order generation complete")
    except :
        print("Exception caught" )
        raise
    
    return

if __name__ == "__main__":
	main()