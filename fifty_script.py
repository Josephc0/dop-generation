import pandas as pd 

from influxdb import InfluxDBClient

#connect to influx

client = InfluxDBClient(host = "localhost", port = 8086)
client.switch_database("mydopdb")


# function to query data
def query_fifty():
    result = []
    limit = 1
    for offset in range(49,10000,50):
        query = f"SELECT * FROM dop LIMIT {limit} OFFSET {offset}"
        result_query = client.query(query)
        result.extend(list(result_query.get_points()))

    return result


data = query_fifty()
for point in data:
        print(point)