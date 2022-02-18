import logging
import sys

from couchbase.cluster import Cluster, PasswordAuthenticator

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# open cluster and authenticate as Cluster Admin
cluster = Cluster('couchbase://localhost:8091')

print ('Authenticator as Administrator.')
cluster.authenticate(PasswordAuthenticator('Administrator', 'password'))

# Create a user and assign roles
manager = cluster.cluster_manager()
manager.user_upsert('cbtestuser', 'cbtestuserpwd', [
    # Roles required for the reading of data from the bucket
    ('data_reader', 'travel-sample'),
    ('query_select', 'travel-sample'),

    # Roles required for the writing of data into the bucket
    ('data_writer', 'travel-sample'),
    ('query_insert', 'travel-sample'),
    ('query_delete', 'travel-sample'),

    # Role required for the creation of indexes on the bucket
    ('query_manage_index', 'travel-sample')
    ], 'cbtestuser')

print ('Listing current users.')
users = manager.users_get().value

for index, user in enumerate(users):
    print ('user {0}'.format(index))
    print ('user\'s name is {0}'.format(user.get('name')))
    print ('user\'s domain is {0}'.format(user.get('domain')))

    for role in user.get('roles'):
        print ('User has the role: {0}, applicable to bucket {1}'.format(role.get('role'), role.get('bucket_name')))

print ('Authenticating as user.')
cluster = Cluster('couchbase://localhost:8091')
cluster.authenticate(PasswordAuthenticator('cbtestuser', 'cbtestuserpwd'))

print ('Opening travel-sample bucket as user.')
bucket = cluster.open_bucket('travel-sample')

# Create a N1QL Primary Index (but ignore if one already exists).
bucket.bucket_manager().create_n1ql_primary_index(defer=False, ignore_exists=True)

print ('Reading out airline_10 document.')
airline = bucket.get('airline_10')

print ('Found: {0}'.format(airline.value))

print ('Upserting new document as user.')
bucket.upsert('airline_11',
    {'callsign': 'MILE-AIR',
    'iata': 'Q5',
    'icao': 'MLA',
    'id': 11,
    'name': '40-Mile Air',
    'type': 'airline'})

print ('Reading out airline_11 document.')
airline = bucket.get('airline_11')

print ('Found: {0}'.format(airline))

print ('Performing query as user.')
value = 'Query-results are:'

result = bucket.n1ql_query('SELECT * FROM `travel-sample` LIMIT 5')
for row in result:
    value += '\n\t{0}'.format(row)

print (value)


print ('Re-authenticating as administrator.')
cluster = Cluster('couchbase://localhost:8091')
cluster.authenticate(PasswordAuthenticator('Administrator', 'password'))

print ('Removing user as administrator.')
user_to_remove = 'cbtestuser'
removed = cluster.cluster_manager().user_remove(user_to_remove)

if removed.success:
    print ('Deleted user {0}.'.format(user_to_remove))
else:
    print ('Could not delete user {0}.'.format(user_to_remove))