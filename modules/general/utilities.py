import os
import typing as T
import modules.general.constants
import math
import concurrent.futures
import time
import re


def build_path(dir: str = ""):
    path = str(os.path.dirname((os.path.realpath(__file__))))
    path = path + "/" + dir
    return path.replace("\\", "/")


def get_root_directory():
    sep_path = build_path().split("/")
    root_sep_path = sep_path[: sep_path.index(modules.general.constants.PROJ_NAME) + 1]
    return "/".join(root_sep_path)


def coalesce(source: T.Dict[str, str], target: T.Dict[str, str]):
    for key in target:
        value = target[key] if (target[key] or key not in source) else source[key]
        target[key] = value
    return target


def split_chunks(
    iterables: T.Iterable[T.Any], size=modules.general.constants.PARALLEL
) -> T.Tuple[T.Iterable]:
    num_of_chunks = math.ceil(len(iterables) / size)
    return tuple(
        iterables[idx * size : (idx + 1) * size] for idx in range(num_of_chunks)
    )


def clean_text(remove_chars: T.List[str], text: str):
    new_text = text
    for remove_char in remove_chars:
        new_text = re.sub(remove_char, "", new_text)
    return new_text


def parallelize(
    iterables: T.Iterable,
    function: T.Callable,
    timeout: int = None,
    idle_time: float = 4,
    concurrency: int = modules.general.constants.PARALLEL,
):
    print("Parallelism factor:", concurrency)
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        step = concurrency
        idx = 0
        output = []
        while True:
            iterable = iterables[idx * step : (idx + 1) * step]
            if len(iterable):
                for res in executor.map(function, iterable, timeout=timeout):
                    output.append(res)
                idx += 1
                time.sleep(idle_time)
            else:
                break
        return output
