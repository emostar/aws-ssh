import logging

from boto import ec2
from boto.exception import EC2ResponseError

from errors import UnknownAWSInstance

def find_region(id):
    regions = ec2.regions()
    for region in regions:
        conn = region.connect()
        logging.info('Searching in region %s' % conn.region.name)
        try:
            instances = conn.get_all_instances(instance_ids=[id])
            if len(instances):
                return conn.region
        except EC2ResponseError:
            pass
    raise UnknownAWSInstance(id)


def get_from_regions(tags, region=None):
    """
    Search for all instances that match the tags specifed. If the regions
    parameter is None, then every region is searched, otherwise each the region
    specified is searched. To search more than one region, pass in a list of
    regions for region.
    """
    def get_from_one_region(conn, tags):
        instances = []
        logging.info('Searching in region %s' % conn.region.name)
        reservations = conn.get_all_instances(filters=tags)
        for reservation in reservations:
          for instance in reservation.instances:
              instances.append(instance)
        return instances

    instances = []
    if region is None:
        regions = ec2.regions()
        for region in regions:
            conn = region.connect()
            instances += get_from_one_region(conn, tags)
    else:
        if not isinstance(region, list):
            region = [region]

        for r in region:
            conn = r.connect()
            instances += get_from_one_region(conn, tags)

    if len(instances) == 0:
        raise Exception('No instances found')

    return instances


if __name__ == '__main__':
    import sys
    region = find_region(sys.argv[1])
    print region.name
