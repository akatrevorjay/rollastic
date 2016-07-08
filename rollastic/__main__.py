from rollastic.log import get_logger

_LOG = get_logger()

from rollastic.cluster import Cluster
from rollastic.salty import get_saltcli
import click


@click.group()
def cli():
    pass


@cli.command()
@click.argument('master_node', nargs=1)
@click.option('--masters/--no-masters', default=False, help='Restart master nodes as well [false]')
@click.option('--datas/--no-datas', default=True, help='Restart data nodes [true]')
@click.option('--kill-at-heap', default=85, help='Heap used percentage threshold to restart that node [85]',
              type=click.INT)
@click.option('--pepper-url', help='Salt API URL (if unset, assume on Salt master)')
@click.option('--pepper-username', default='rollastic', help='Salt API username [rollastic]')
@click.option('--pepper-password', default='', help='Salt API password [unset]')
@click.option('--pepper-eauth', default='pam', help='Salt API authentication method [pam]')
@click.option('--pepper-ignore-ssl-errors', default=False, help='Ignore bad Salt API SSL certificate [false]',
              type=click.BOOL)
@click.option('--pepper-debug', default=False, help='Debug Salt API communication',
              type=click.BOOL)
def restart(master_node, masters, datas, kill_at_heap,
            pepper_url, pepper_username, pepper_password, pepper_eauth,
            pepper_ignore_ssl_errors, pepper_debug):
    '''
    Rolling restart of cluster.

    MASTER_NODE is the initial node to query to get the list of master nodes to connect to. Rollastic will connect to all master nodes to avoid relying on one to be up for the roll procedure.

    \b
    This will:
      - Collect and order the nodes to roll.
        If you opted to include master nodes, they are always done first.
      - Wait until cluster is in green health
      - For each node from #1 above
        If node's heap used percentage is over kill-at-heap:
        * Disable cluster allocation
        * Ping node through Salt to verify connectivity
        * Shutdown node
        * Wait for ES to die for 2m.
          If it's not dead, run a killall java and wait another 2m.
          If it's still not dead, fail.
        * Start elasticsearch service through Salt
        * Wait until node joins cluster with an uptime within 120s.
        * Enable allocation
        * Wait until cluster is in green health
    '''
    _LOG.info('Rolling restart with master_node=%s kill_at_heap=%s', master_node, kill_at_heap)

    cluster = Cluster(master_node)
    _LOG.info('Cluster status: %s', cluster.status())

    saltcli = get_saltcli(api_url=pepper_url,
                          username=pepper_username, password=pepper_password,
                          eauth=pepper_eauth,
                          ignore_ssl_errors=pepper_ignore_ssl_errors,
                          debug_http=pepper_debug)

    cluster.rolling_restart(master=masters, data=datas, heap_used_percent_threshold=kill_at_heap,
                            saltcli=saltcli)


@cli.command()
@click.argument('master_node', nargs=1)
@click.option('--masters/--no-masters', default=False, help='Restart master nodes as well [false]')
@click.option('--datas/--no-datas', default=True, help='Restart data nodes [true]')
@click.option('--minimum-version', default='1.7.1', help='Minimum version to upgrade to [1.7.1]')
@click.option('--pepper-url', help='Salt API URL (if unset, assume on Salt master)')
@click.option('--pepper-username', default='rollastic', help='Salt API username [rollastic]')
@click.option('--pepper-password', default='', help='Salt API password [unset]')
@click.option('--pepper-eauth', default='pam', help='Salt API authentication method [pam]')
@click.option('--pepper-ignore-ssl-errors', default=False, help='Ignore bad Salt API SSL certificate [false]',
              type=click.BOOL)
@click.option('--pepper-debug', default=False, help='Debug Salt API communication',
              type=click.BOOL)
def upgrade(master_node, masters, datas, minimum_version,
            pepper_url, pepper_username, pepper_password, pepper_eauth,
            pepper_ignore_ssl_errors, pepper_debug):
    '''
    Rolling upgrade of cluster.

    MASTER_NODE is the initial node to query to get the list of master nodes to connect to. Rollastic will connect to all master nodes to avoid relying on one to be up for the roll procedure.

    \b
    This will:
      - Collect and order the nodes to roll.
        If you opted to include master nodes, they are always done first.
      - Wait until cluster is in green health
      - For each node from #1 above
        If node's ES version is under minimum_version:
        * Disable cluster allocation
        * Ping node through Salt to verify connectivity
        * Run a Salt highstate
        * Check for an available upgrade on the Elasticsearch package, if so:
          - Shutdown node
          - Wait for ES to die for 2m.
            If it's not dead, run a killall java and wait another 2m.
            If it's still not dead, fail.
        * If ES was stopped at any point in this:
          - Start elasticsearch service if it's not already started
          - Wait until node joins cluster with an uptime within 120s.
        * Enable allocation
        * Wait until cluster is in green health
    '''
    _LOG.info('Rolling upgrade with master_node=%s and minimum_version=%s', master_node, minimum_version)

    cluster = Cluster(master_node)
    _LOG.info('Cluster status: %s', cluster.status())

    saltcli = get_saltcli(api_url=pepper_url,
                          username=pepper_username, password=pepper_password,
                          eauth=pepper_eauth,
                          ignore_ssl_errors=pepper_ignore_ssl_errors,
                          debug_http=pepper_debug)

    cluster.rolling_upgrade(master=masters, data=datas, minimum_version=minimum_version,
                            saltcli=saltcli)


if __name__ == '__main__':
    cli(auto_envvar_prefix='ROLLASTIC')
