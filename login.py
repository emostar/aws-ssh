import getpass
import logging
import os
import sys

from boto import ec2 
from boto.exception import EC2ResponseError

import paramiko

from finder import find_region, get_from_regions
import interactive

class Client(object):
    def __init__(self, region=None):
        self.instance_id = None
        self.ip_address = None
        self.instance = None

        if region is None:
            # Delay the region search
            self.region = None
            self.conn = None
        else:
            region_list = [r for r in ec2.regions() if r.name == region]
            if len(region_list) == 0:
                raise Exception('Unknown region: %s' % self.region)
            self.region = region_list.pop()

            # Open a connection to the API
            self.conn = self.region.connect()

    def by_instance_id(self, id):
        # Search for a region if we don't have one specified
        if self.region is None:
            self.region = find_region(id)
            self.conn = self.region.connect()

        self.instance_id = id

        # Get the IP address of the instance now
        self.get_ip_address(instance_ids=[self.instance_id])

    def by_tag(self, tags):
        filters = dict()
        for tag in tags:
            name,value = tag.split("=")
            filters['tag:'+name] = value

        instances = get_from_regions(filters, self.region)
        return instances

    def login(self, instance_id=None, tags=None):
        if instance_id is not None:
            self.by_instance_id(instance_id)
        elif tags is not None:
            instances = self.by_tag(tags)
            if len(instances) > 1:
                raise Exception('You can only login to one instance. For'
                    'multiple instances you can specify a command to run.')
            self.ip_address = instances[0].ip_address

        # Get terminal size
        # FIXME Support terminal resizing
        rows,columns = os.popen('stty size', 'r').read().split()

        try:
            # Connect to the host
            client = self._connect_client(self.ip_address)
            chan = client.invoke_shell(width=int(columns), height=int(rows))
            # Start an interactive shell
            interactive.interactive_shell(chan)

            # Close everything after logout
            chan.close()
            self._close_client(client)
        except Exception, e:
            print '*** Caught exception: %s: %s' % (e.__class__, e)
            try:
                self._close_client(client)
            except:
                pass
            sys.exit(1)

    def run_command(self, cmd, instance_ids=None, tags=None):
        if instance_ids is not None:
            instances = self.by_instance_id(instance_ids)
        elif tags is not None:
            instances = self.by_tag(tags=tags)
        else:
            raise Exception('Missing parameter')

        ip_addresses = [i.ip_address for i in instances]

        for ip_address in ip_addresses:
            try:
                client = self._connect_client(ip_address)
                stdin,stdout,stderr = client.exec_command(cmd)
                for line in stdout:
                    print '[%s]: %s' % (ip_address, line.strip('\n'))
                self._close_client(client)
            except Exception, e:
                print '*** Error encountered with host: %s [%s]' % (ip_address, e)
                try:
                    self._close_client(client)
                except:
                    pass

    def get_ip_address(self, instance_ids=None, filters=None):
        instances = self.get_instance(instance_ids, filters)
        self.ip_address = instances[0].ip_address
        return self.ip_address

    def get_instance(self, instance_ids=None, filters=None):
        if instance_ids is not None:
            reservations = self.conn.get_all_instances(instance_ids=instance_ids)
        elif filters is not None:
            reservations = self.conn.get_all_instances(filters=filters)
        else:
            raise Exception('Missing parameter')

        instances = []
        for reservation in reservations:
          for instance in reservation.instances:
              instances.append(instance)
        return instances

    def _connect_client(self, ip_address):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy)
        logging.debug('Connecting to %s...' % ip_address)
        client.connect(ip_address)
        logging.debug('Connected')
        return client

    def _close_client(self, client):
        client.close()


if __name__ == '__main__':
    import sys
    client = Client()
    #client.login(instance_id=sys.argv[1])
    client.run_command('which curl', tags=[("System", "sekaicafe")])
