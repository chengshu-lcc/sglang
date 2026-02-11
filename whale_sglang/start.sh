#!/bin/bash
# 去掉boot.sh里和install whl/requirments有关的逻辑，仅保留启动服务刷log的功能

set -x;

SCRIPT_PATH="$( cd "$(dirname "$0")" || return ; pwd -P )"

if [ -z "${HIPPO_PROC_WORKDIR}" ]; then
  export TEMP_HIPPO_DIR=/tmp/hippo_temp
  mkdir -p $TEMP_HIPPO_DIR
  HIPPO_PROC_WORKDIR=$TEMP_HIPPO_DIR
fi

if [ -z "${HIPPO_APP_INST_ROOT}" ]; then
  export HIPPO_APP_INST_ROOT=$SCRIPT_PATH/../../
fi

DEFAULT_START_PORT=12233;
DEFAULT_PY_RTP_LOG_KEEP_COUNT=50;

if [ -z "${START_PORT}" ]; then
  export START_PORT=$DEFAULT_START_PORT
fi

PY_RTP_LOG_KEEP_COUNT=${PY_RTP_LOG_KEEP_COUNT:-${DEFAULT_PY_RTP_LOG_KEEP_COUNT}};

export LOG_DIR="$HIPPO_PROC_WORKDIR"/logs;
mkdir -p "$LOG_DIR";
ls $LOG_DIR | grep -Ev '[0-9]{4}_[0-9]{2}_[0-9]{2}__' | \
xargs -I {} bash -c 'mv ${LOG_DIR}/{} ${LOG_DIR}/`date -r ${LOG_DIR}/{} +"%Y_%m_%d__%H_%M_%S__"`{}';
ls ${LOG_DIR} -t | tail -n +${PY_RTP_LOG_KEEP_COUNT} | xargs -I {} rm -rf ${LOG_DIR}/{};

# $LOG_PATH used for py_inference `get_handler` func, do not remove
export LOG_PATH=$LOG_DIR

export STDOUT_FILE=$LOG_DIR/stdout
export STDERR_FILE=$LOG_DIR/stderr
export ENV_FILE=$LOG_DIR/env.txt

#logging level
export LOG_LEVEL="INFO"

# pyfsutil
export HADOOP_HOME=$HIPPO_APP_INST_ROOT/usr/local/hadoop/hadoop;
export JAVA_HOME=$HIPPO_APP_INST_ROOT/usr/local/java/jdk;
export FSLIB_DFS_STORAGE_LINKS=${HIPPO_ENV_STORAGE_LINKS-"dir|pov|alb"};
export PATH=$JAVA_HOME/bin:$PATH;
FSUTIL_DIR=$HIPPO_APP_INST_ROOT;

HOST_DRIVER_VERSION=${HOST_NVIDIA_DRIVER_VERSION}
# 如果环境变量为空，尝试通过 nvidia-smi 获取驱动版本
if [ -z "$HOST_DRIVER_VERSION" ]; then
  if command -v nvidia-smi &> /dev/null; then
    # 使用nvidia-smi获取驱动版本
    HOST_DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits | head -n 1)
    if [ $? -eq 0 ] && [ -n "$NVIDIA_DRIVER_VERSION" ]; then
      HOST_DRIVER_VERSION=$NVIDIA_DRIVER_VERSION
    fi
  fi
fi

PPU_SDK_PATH=/usr/local/PPU_SDK
if [ ! -d "${PPU_SDK_PATH}" ]; then
  PPU_SDK_PATH=/usr/local/PPU_SDK_CUDA_11.8_PyTorch2.0_alios7-py310/PPU_SDK
fi
BASE_LD_LIBRARY_PATH="${PPU_SDK_PATH}/lib:${PPU_SDK_PATH}/CUDA_SDK/lib64"

COMPAT_CUDA_PATH="/usr/local/cuda/compat/"

ADDITIONAL_LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/lib64:/usr/local/nvidia/lib64/:\
${HIPPO_APP_INST_ROOT}/usr/lib64/nvidia/:\
${HIPPO_APP_INST_ROOT}/usr/local/cuda/lib64:/usr/local/cuda/lib64/:\
${HIPPO_APP_INST_ROOT}/inference_sdk/lib:\
${HIPPO_APP_INST_ROOT}/opt/taobao/java/jre/lib/amd64/server/:\
${FSUTIL_DIR}/lib:${FSUTIL_DIR}/lib64:${FSUTIL_DIR}/usr/local/lib:${FSUTIL_DIR}/usr/local/lib64"

NEED_COMPAT_CUDA_PATH=1
# 判断 HOST_NVIDIA_DRIVER_VERSION 是否为空
if [ -n "$HOST_DRIVER_VERSION" ]; then
  # 提取版本号
  major_version=$(echo "$HOST_DRIVER_VERSION" | cut -d '.' -f 1)
  minor_version=$(echo "$HOST_DRIVER_VERSION" | cut -d '.' -f 2)

  # 检查前两位版本号是否 >= 535
  if [ "$major_version" -ge 535 ]; then
    # 去掉LD_LIBRARY_PATH中的 /usr/local/cuda/compat/
    ADDITIONAL_LD_LIBRARY_PATH=$(echo "$ADDITIONAL_LD_LIBRARY_PATH" | sed 's|:/usr/local/cuda/compat/||')
    NEED_COMPAT_CUDA_PATH=0
  fi
fi

if [ "$NEED_COMPAT_CUDA_PATH" -eq 1 ]; then
  FIXED_LD_LIBRARY_PATH="$BASE_LD_LIBRARY_PATH:$COMPAT_CUDA_PATH:$ADDITIONAL_LD_LIBRARY_PATH"
else
  FIXED_LD_LIBRARY_PATH="$BASE_LD_LIBRARY_PATH:$ADDITIONAL_LD_LIBRARY_PATH"
fi

export LD_LIBRARY_PATH="$FIXED_LD_LIBRARY_PATH"
export LD_LIBRARY_PATH_SETTED=1;

export FSLIB_PANGU_ENABLE_SEQUENTIAL_READAHEAD=${FSLIB_PANGU_ENABLE_SEQUENTIAL_READAHEAD-"true"}
export FSLIB_PANGU_ENABLE_BUFFER_WRITE=${FSLIB_PANGU_ENABLE_BUFFER_WRITE-"true"}

echo "START_PORT=${START_PORT}";

export PY_INFERENCE_LOG_RESPONSE=1

# setting vllm config
EXTRA_CMD="${EXTRA_CMD:+$EXTRA_CMD }--trust-remote-code"

if [[ -z "${REUSE_CACHE}" ]]; then
  echo "REUSE_CACHE is not set, set it to 0"
  REUSE_CACHE=0
fi

if [[ -z "${TOKENIZER_MODE}" ]]; then
  echo "TOKENIZER_MODE is not set, set it to 0"
  TOKENIZER_MODE="auto"
fi

if [[ "${REUSE_CACHE}" == "0" ]]; then
  echo "REUSE_CACHE is set to 0, will disable cache"
  EXTRA_CMD="${EXTRA_CMD} --disable-radix-cache"
fi

if [ -n "$QUANTIZATION" ]; then
    QUANTIZATION_ARG="--quantization ${QUANTIZATION}"
    EXTRA_CMD="${EXTRA_CMD} ${QUANTIZATION_ARG}"
fi

if [[ -z "${CONFIG_FORMAT}" ]]; then
  echo "CONFIG_FORMAT is not set, set it to auto"
  CONFIG_FORMAT="auto"
fi

if [[ -z "${LOAD_FORMAT}" ]]; then
  echo "LOAD_FORMAT is not set, set it to auto"
  LOAD_FORMAT="auto"
fi

if [[ -z "${DTYPE}" ]]; then
  echo "DTYPE is not set, set it to auto"
  DTYPE="auto"
fi

if [[ -z "${TASK}" ]]; then
  echo "TASK is not set, set it to auto"
  TASK="auto"
fi

if [[ -z "${KV_CACHE_DTYPE}" ]]; then
  echo "KV_CACHE_DTYPE is not set, set it to auto"
  KV_CACHE_DTYPE="auto"
fi

if [[ -z "${GPU_MEMORY_UTILIZATION}" ]]; then
  echo "GPU_MEMORY_UTILIZATION is not set, set it to 0.8"
  GPU_MEMORY_UTILIZATION="0.8"
fi

if [[ -z "${MAX_WATCHDOG_TIMEOUT}" ]]; then
  echo "MAX_WATCHDOG_TIMEOUT is not set, set it to 300"
  MAX_WATCHDOG_TIMEOUT="300"
fi

printenv > "$ENV_FILE";
if [ "${CMD}" ]; then
    echo "use cmd mode"
    ${CMD} >> "$STDOUT_FILE" 2>> "$STDERR_FILE";
else
    echo "use default mode"
    # 尝试使用指定的 Python 路径
    if [ -x /opt/conda310/bin/python3 ]; then
      PYTHON_EXEC=/opt/conda310/bin/python3
    # 检查 /opt/conda//envs/py_3.9/bin/python 是否存在
    elif [ -f /opt/conda//envs/py_3.9/bin/python ]; then
        PYTHON_EXEC=/opt/conda//envs/py_3.9/bin/python
    else
        # 使用系统的 python3
        echo "/opt/conda310/bin/python3 not found and /opt/conda//envs/py_3.9/bin/python not found, using system python3"
        PYTHON_EXEC=python3
    fi

    $PYTHON_EXEC -s -m sglang_server.server.start_server \
      --port ${START_PORT} \
      --model-path ${CHECKPOINT_PATH} \
      --tokenizer-path ${CHECKPOINT_PATH} \
      --tokenizer-mode ${TOKENIZER_MODE} \
      --load-format ${LOAD_FORMAT} \
      --trust-remote-code \
      --dtype ${DTYPE} \
      --kv-cache-dtype ${KV_CACHE_DTYPE} \
      --served-model-name rtp \
      --max-running-requests ${CONCURRENCY_LIMIT} \
      --tp-size ${TP_SIZE} \
      --enable-metrics \
      --context-length ${MAX_SEQ_LEN} \
      --mem-fraction-static ${GPU_MEMORY_UTILIZATION} \
      --watchdog-timeout ${MAX_WATCHDOG_TIMEOUT} \
      --host 0.0.0.0 \
      ${EXTRA_CMD} >> "$STDOUT_FILE" 2>> "$STDERR_FILE"
fi
