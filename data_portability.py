"""Demo script for downloading data through the Data Portability API.

Gets an OAuth token, initiates a portability archive, polls status, gets signed
URLs, downloads archive, and then resets authorization.

Usage:
python3 data-portability-quickstart.py
python3 data-portability-quickstart.py --start_time 2024-01-01T00:00:00Z
--end_time 2024-12-31T23:59:59Z --resources myactivity.search myactivity.youtube
"""

import argparse
from collections.abc import Sequence
import io
import itertools
import json
import os
import pathlib
import time
from typing import Generator, TypeAlias
import urllib
import zipfile

from google.auth import exceptions
from google.auth.transport import requests
from google.oauth2 import credentials
import google_auth_oauthlib.flow
from googleapiclient import discovery
import googleapiclient.errors

# The name of a file that contains the OAuth 2.0 information for this
# application, including the client_id and client_secret. For this script, this
# should be a desktop application OAuth client.
CLIENT_SECRETS_FILE = 'f:\\Users\\matts\\Downloads\\client_secret_861635085591-g8fgcbrcfa95ei74881508g04dfmffmi.apps.googleusercontent.com.json'
TOKENS_PATH = 'token'

# A list of Data Portability resources that we want to request.
RESOURCES = ['myactivity.search', 'dataportability.alerts.subscriptions']

DATAPORTABILITY_API_SERVICE_NAME = 'dataportability'
API_VERSION = 'v1'

# There is a one to one mapping between Data Portability resources and
# dataportability OAuth scopes. The scope code is the resource name plus a
# prefix.
SCOPE_PREFIX = 'https://www.googleapis.com/auth/dataportability.'


def _get_next_token_index() -> int:
  indices = [
      int(pathlib.Path(token_path).stem)
      for token_path in os.listdir(TOKENS_PATH)
  ]
  return max(indices, default=0) + 1


def store_credentials(creds: credentials.Credentials) -> str:
  """Stores OAuth 2.0 credentials as json file for reuse.

  Args:
    creds: Credentials generated through an OAuth flow.

  Returns:
    The path of the stored credentials file.
  """

  index = _get_next_token_index()
  credsfile = os.path.join(TOKENS_PATH, f'{index}.json')
  with open(credsfile, 'w') as token:
    token.write(creds.to_json())
  return credsfile


CredentialsInfo: TypeAlias = tuple[credentials.Credentials, Sequence[str], str]


def load_credentials(resources: Sequence[str]) -> CredentialsInfo | None:
  """Loads already granted OAuth 2.0 credentials if possible."""
  scopes = {SCOPE_PREFIX + r for r in resources}
  # Try to use an already granted token if we have a valid one for the requested
  # scopes.
  for name in os.listdir(TOKENS_PATH):
    path = os.path.join(TOKENS_PATH, name)
    with open(path, 'r') as f:
      token = json.load(f)
      if scopes <= set(token['scopes']):
        try:
          creds = credentials.Credentials.from_authorized_user_file(
              path, scopes
          )
          if creds and creds.expired and creds.refresh_token:
            creds.refresh(requests.Request())
          print('Using existing credentials')
          return creds, resources, path
        except exceptions.RefreshError:
          print('Deleting expired or revoked credentials: ', path)
          os.remove(path)


def credentials_from_partial_grant(warn: Warning) -> CredentialsInfo:
  """Gets credentials from a partial grant."""
  with open(CLIENT_SECRETS_FILE, 'r') as f:
    with open(CLIENT_SECRETS_FILE, 'r') as f:
      client_secrets = json.load(f)['installed']
      creds = credentials.Credentials(
          # The warning raised by the flow contains the access token, refresh
          # token, and the scopes selected by the user.
          warn.token['access_token'],
          refresh_token=warn.token['refresh_token'],
          scopes=warn.new_scope,
          client_id=client_secrets['client_id'],
          client_secret=client_secrets['client_secret'],
      )
      return (
          creds,
          [scope.removeprefix(SCOPE_PREFIX) for scope in warn.new_scope],
          store_credentials(creds),
      )


def get_credentials(resources: Sequence[str]) -> CredentialsInfo:
  """Gets OAuth 2.0 credentials using an installed app OAuth flow.

  This generates a link for the user to consent to some or all of the requested
  resources. In a production environment, the best practice is to save a refresh
  token in Cloud Storage because the access token can expire before the
  portability archive job completes.

  Args:
    resources: A list of dataportability resource IDs. These are OAuth scope
      codes from
      https://developers.google.com/data-portability/reference/rest/v1/portabilityArchive/initiate#authorization-scopes
        without the 'https://www.googleapis.com/auth/dataportability.' prefix.

  Returns:
    A tuple of credentials containing an access token, a list of resources
    for which the user has granted consent, and the path of the stored
    credentials file.
  """
  existing_creds = load_credentials(resources)
  if existing_creds is not None:
    return existing_creds

  scopes = {SCOPE_PREFIX + r for r in resources}
  flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, list(scopes)
  )
  try:
    creds = flow.run_local_server(
        port=0,
        open_browser=False,
    )
    return creds, resources, store_credentials(creds)
  except Warning as warn:
    # We should gracefully handle the user only consenting to a subset of the
    # requested scopes.
    return credentials_from_partial_grant(warn)


def get_api_interface(
    creds: credentials.Credentials,
) -> discovery.Resource:
  """Gets an interface to the Data Portability API."""

  return discovery.build(
      serviceName=DATAPORTABILITY_API_SERVICE_NAME,
      version=API_VERSION,
      credentials=creds,
  )


def initiate_portability_archive(
    dataportability: discovery.Resource,
    resources: Sequence[str],
    start_time: str,
    end_time: str,
) -> str:
  """Initiates a portability archive for the requested resources and optional start and end time."""
  request_body = {'resources': resources}
  if start_time:
    request_body['start_time'] = start_time
  if end_time:
    request_body['end_time'] = end_time
  initiate = dataportability.portabilityArchive().initiate(body=request_body)
  print('\n', initiate.method, initiate.body, initiate.uri, '\n')
  initiate_response = initiate.execute()
  print(initiate_response, '\n')
  return initiate_response['archiveJobId']


def exponential_backoff(
    delay: float, max_delay: float, multiplier: float
) -> Generator[None, None, None]:
  while True:
    time.sleep(delay)
    yield
    delay = min(delay * multiplier, max_delay)


def poll_get_portability_archive_state(
    dataportability: discovery.Resource, job_id: str
) -> Sequence[str]:
  """Calls dataportability's getPortabilityArchiveState endpoint."""
  get_state = dataportability.archiveJobs().getPortabilityArchiveState(
      name='archiveJobs/{}/portabilityArchiveState'.format(job_id)
  )
  print(
      'Polling archive status while server indicates state is in progress...\n',
      get_state.method,
      get_state.uri,
  )
  for _ in exponential_backoff(3, 3600, 1.5):
    state = get_state.execute()
    print(state)
    if state['state'] != 'IN_PROGRESS':
      return state['urls']


def print_most_recent_activity(zf: zipfile.ZipFile) -> None:
  """Prints the most recent My Activity event from the archive.

  Args:
    zf: A ZipFile containing one or more 'MyActivity.json' exports.
  """
  try:
    most_recent_item = max(
        itertools.chain.from_iterable(
            json.loads(zf.read(info))
            for info in zf.infolist()
            if 'My Activity' in info.filename
        ),
        key=lambda x: x['time'],
    )
    print('\nMost recent activity:\n', most_recent_item['title'])
  except ValueError:
    # No My Activity events.
    pass


def is_job_already_exists_error(e: googleapiclient.errors.HttpError) -> bool:
  """Checks if the error indicates that a job with the same ID already exists."""
  return e.error_details[0]['reason'] in [
      'ALREADY_EXISTS_ONE_TIME',
      'ALREADY_EXISTS_TIME_BASED',
  ]


def job_id_already_exists(e: googleapiclient.errors.HttpError) -> str:
  """Extracts the job ID from an ALREADY_EXISTS error."""
  return e.error_details[0]['metadata']['job_id']


def is_resource_exhausted_error(e: googleapiclient.errors.HttpError) -> bool:
  return e.error_details[0]['reason'] in [
      'RESOURCE_EXHAUSTED_ONE_TIME',
      'RESOURCE_EXHAUSTED_TIME_BASED',
  ]


def job_ids_resource_exhausted(
    e: googleapiclient.errors.HttpError,
) -> Sequence[str]:
  """Extracts the previous job IDs from a RESOURCE_EXHAUSTED error."""
  return e.error_details[0]['metadata']['previous_job_ids']


def timestamp_after_cooldown_period(
    e: googleapiclient.errors.HttpError,
) -> str:
  """Extracts the timestamp after the cooldown period from a RESOURCE_EXHAUSTED_TIME_BASED error."""
  return e.error_details[0]['metadata']['timestamp_after_24hrs']


def main() -> None:
  # When running locally, disable OAuthlib's HTTPs verification. When
  # running in production *do not* leave this option enabled.
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
  parser = argparse.ArgumentParser(
      description='Process start_time and/or end_time.'
  )
  parser.add_argument(
      '--start_time',
      action='store',
      required=False,
      type=str,
      help='Enter your start time in YYYY-MM-DDTHH:MM:SSZ format (optional)',
  )
  parser.add_argument(
      '--end_time',
      action='store',
      required=False,
      type=str,
      help='Enter your end time in YYYY-MM-DDTHH:MM:SSZ format (optional)',
  )
  parser.add_argument(
      '--resources',
      action='store',
      required=False,
      nargs='+',
      type=str,
      help='Enter the resource groups to export (optional)',
  )
  args = parser.parse_args()
  start_time = args.start_time
  end_time = args.end_time
  resources = args.resources if args.resources else RESOURCES
  try:
    job_id = None
    dataportability = None
    while job_id is None:
      creds, resources, credsfile = get_credentials(resources)
      print()
      print('Obtained OAuth credentials for resources: ', ', '.join(resources))
      dataportability = get_api_interface(creds)
      try:
        job_id = initiate_portability_archive(
            dataportability, resources, start_time, end_time
        )
        print('Successfully initiated data archive job with ID', job_id, '\n')
      except exceptions.RefreshError:
        # We can hit a RefreshError here rather than in get_credentials if the
        # user revoked the grant before the access token expired.
        print('Deleting expired or revoked credentials: ', credsfile)
        os.remove(credsfile)
      except googleapiclient.errors.HttpError as e:
        # We can hit an ALREADY_EXISTS error if the user attempts to initiate
        # new job while the previous identical job is still in progress.
        if is_job_already_exists_error(e):
          job_id = job_id_already_exists(e)
          print(e, '\n')
          print(f'Downloading data archive for preexisting job: {job_id} \n')
        # We can hit a RESOURCE_EXHAUSTED error if the user attempts to initiate
        # new job with the exhausted resources.
        elif is_resource_exhausted_error(e):
          previous_job_ids = job_ids_resource_exhausted(e)
          if e.error_details[0]['reason'] == 'RESOURCE_EXHAUSTED_TIME_BASED':
            print(
                f'Resource exhausted under previous job(s): {previous_job_ids}.'
                f' Please wait until {timestamp_after_cooldown_period(e)} to'
                ' initiate a new job.\n'
            )
          elif e.error_details[0]['reason'] == 'RESOURCE_EXHAUSTED_ONE_TIME':
            print(
                f'Resource exhausted under previous job(s): {previous_job_ids}.'
            )
          else:
            print('Resource exhausted error with unknown reason.\n')
          raise
    urls = poll_get_portability_archive_state(dataportability, job_id)
    for url in urls:
      print('\nData archive is ready. Beginning download.')
      ufile = urllib.request.urlopen(url)
      print('Download complete! Extracting archive...\n')
      zf = zipfile.ZipFile(io.BytesIO(ufile.read()), 'r')
      for f in zf.filelist:
        print(f)
      print_most_recent_activity(zf)
      # Save extracted files in the current directory.
      zf.extractall()
  except googleapiclient.errors.HttpError as e:
    print(e)


if __name__ == '__main__':
  main()