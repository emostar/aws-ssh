# Ideal Commands

```
awssh <instance-id> --region ap-northeast-1
awssh -t System=custom-tag-value uptime
awssh <instance-id>

awsfinder <instance-id>
```

## awsfinder

*Goal*: Find which region an instance is in

* Get specified instance-id
* Query each region in order

## aws-ssh

*Goal*: Login via instance-id

        - Get specified instance-id
        - Login to external IP

        Features:
                Auto Firewall
                  - Specify auth flag
                  - Calls ec2-auth to allow our external IP to ssh into the remote machine
                  - Calls ec2-revoke after login is completed
                Region Finder
                  - Find the region it is in
                Login via Tag
                        - Get specified tag
                        - If more than one instance is returned, fail giving instance ids
