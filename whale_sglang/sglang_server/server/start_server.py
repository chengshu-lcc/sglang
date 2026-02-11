import os
import sys
import logging
import logging.config
import traceback

CUR_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(str(CUR_PATH), '..'))

from config.log_config import LOGGING_CONFIG
from distribute.gang_info import get_gang_info

def local_rank_start(extra_args):
    from server.api_server import start_api_server
    app = None
    try:
        # avoid multiprocessing load failed
        if os.environ.get('FT_SERVER_TEST', None) is None:
            logging.config.dictConfig(LOGGING_CONFIG)
        # reload for multiprocessing.start_method == fork
        start_api_server(extra_args)
    except BaseException as e:
        logging.error(f'start server error: {e}, trace: {traceback.format_exc()}')
        raise e
    return app

def main():
    os.makedirs('logs', exist_ok=True)
    extra_args = []
    if int(os.environ.get("NODE_SIZE", "1")) > 1:
        gang_info: GangInfo = get_gang_info()
        nnodes = len(gang_info.members)
        node_rank = gang_info.self.node_rank
        master = gang_info.master
        dist_init_addr = f"{master.ip}:{master.gang_hb_port}"

        extra_args = ["--dist-init-addr", dist_init_addr, "--nnodes",  str(nnodes), "--node-rank", str(node_rank)]
    logging.info(f"extra_args: [{extra_args}]")
    return local_rank_start(sys.argv[1:] + extra_args)

if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    if os.environ.get('FT_SERVER_TEST', None) is None:
        logging.config.dictConfig(LOGGING_CONFIG)
    main()
