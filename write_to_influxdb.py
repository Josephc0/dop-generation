import os
from influxdb import InfluxDBClient

def init_influxdb_write_client(host: str, username: str, password: str, database: str) -> InfluxDBClient:
      """
      Intialize an InfluxDB client.

      Args:
        host (str): The InfluxDB instance to connect.
        username (str): The InfluxDB username credential to access the InfluxDB instance.
        password (str): The InfluxDB password credential to access the InfluxDB instance.
        database (str): The InfluxDB database to write data to.

      Returns:
        write_influx_client (influxdb.InfluxDBClient) The InfluxDB instance
      """
      write_influxdb_client = InfluxDBClient(
        host=host,
        port=8086,
        username=username,
        password=password,
        ssl=False,
        verify_ssl=False,
        database=database
        )
      return write_influxdb_client

def generate_dop_grid_influxdb_points(time_key: str, dop_file: str, measurement: str) -> list[dict]:
    """
    Reads the DOP metrics output file and converts it to a format that can be written to InfluxDB.

     Args:
        time_key (str): The timestamp of the DOP data.
        dop_file (str): Path to the DOP data file that was generated.
        measurement (str): The InfluxDB measurement to upload the DOP data.

      Returns:
        influx_points (list[dict]): The list of points that can be written to an InfluxDB instance.
      
    """
    influx_points = []
    with open(dop_file, mode='r') as f:
        grid = f.readlines()
    # Remove the first row containing the column names
    grid.pop(0)
    for row in grid:
        values = row.split()
        tags = {
            'Latitude': float(values[0]),
            'Longitude': float(values[1])
        }
        fields = {
            'GDOP': float(values[2]),
            'PDOP': float(values[3]),
            'HDOP': float(values[4]),
            'VDOP': float(values[5]),
            'TDOP': float(values[6]),
            'NUM IN VIEW': float(values[7])
        }
    
        influx_point = {
            "time" : time_key,
            "tags" : tags, 
            "fields" : fields, 
            "measurement" : measurement
        }
        influx_points.append(influx_point)
    return influx_points

def store_influxdb_results(write_influxdb_client: InfluxDBClient, influxdb_points: list[dict], max_batch: int = 1000):
    """
    Stores the DOP metrics onto InfluxDB. Due to the large output size, the data is split into multiple batches to avoid HTTP errors.

     Args:
        write_influxdb_client (influxdb.InfluxDBClient): The InfluxDB instance.
        influxdb_points (list[dict]): The list of points that can be written to an InfluxDB instance.
        max_batch (str, optional): The number of points uploaded at a time. Default is 1000.

    """
    l = len(influxdb_points)
    for start_index in range(0, l, max_batch):
        sub_points = influxdb_points[start_index:start_index + max_batch]
        if not write_influxdb_client.write_points(sub_points):
            print(f'Unable to write points to InfluxDB V1.')
        else:
            print(f'Wrote {len(sub_points)} points to InfluxDB at {write_influxdb_client._host}:{write_influxdb_client._port}.')

# Main entrypoint of the InfluxDB script
if __name__ == "__main__":
    # Read the environment variables
    time_key = os.getenv('TIME_KEY', None)
    dop_file = os.getenv('DOP_OUTPUT_FILE', 'dop_output.txt')
    host = os.getenv('INFLUXDB_WRITE_HOST_V1')
    database = os.getenv('INFLUXDB_WRITE_DB')
    username = os.getenv('INFLUXDB_WRITE_USER')
    password = os.getenv('INFLUXDB_WRITE_PASS')
    measurement = os.getenv('INFLUXDB_WRITE_MEAS_V1', 'dop')
    # Initialize InfluxDB client
    write_influxdb_client = init_influxdb_write_client(host=host, database=database, username=username, password=password)
    # Creates InfluxDB points from the DOP output file
    influxdb_points = generate_dop_grid_influxdb_points(time_key=time_key, dop_file=dop_file, measurement=measurement)
    # Writes the InfluxDB points to an InfluxDB instance
    store_influxdb_results(write_influxdb_client=write_influxdb_client, influxdb_points=influxdb_points)
