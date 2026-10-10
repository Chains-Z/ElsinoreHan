"""在无窗口、错误对话框抑制及超时保护下验证真实负向事件格式器。"""

import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]


def quiet_run(command, *, timeout=30):
    """先设置可继承的 Windows 错误模式，再启动受控子进程，超时杀死并回收。"""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.SetErrorMode.argtypes = [ctypes.c_uint]
    kernel.SetErrorMode.restype = ctypes.c_uint
    mode = 0x8003  # SEM_FAILCRITICALERRORS、SEM_NOGPFAULTERRORBOX、SEM_NOOPENFILEERRORBOX。
    previous = kernel.SetErrorMode(mode)
    try:
        return subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                              creationflags=subprocess.CREATE_NO_WINDOW, timeout=timeout, cwd=ROOT)
    finally:
        kernel.SetErrorMode(previous)


def run_compiled_test(compiled, executable, arguments):
    """即使存在旧产物，编译失败也禁止执行。"""
    if compiled.returncode or not executable.is_file():
        raise RuntimeError("测试编译失败，禁止启动；诊断见 " + str(executable.parent))
    return quiet_run([str(executable)] + [str(p) for p in arguments])


def main():
    if os.name != "nt":
        raise RuntimeError("验证入口仅用于已核对的 Windows x86 CLR 环境")
    build = ROOT / "runtime/build/invited-followup" / uuid.uuid4().hex
    build.mkdir(parents=True)
    managed = Path("D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed")
    # Harmony 的依赖必须完整；不要因编译失败而启动旧测试产物。
    for filename in ("Elsinore.dll", "FSharp.Core.dll"):
        shutil.copyfile(managed / filename, build / filename)
    for source in (ROOT / "runtime/vendor/BepInEx5/BepInEx/core").glob("*.dll"):
        shutil.copyfile(source, build / source.name)
    executable = build / "TestInvitedEventNotice.exe"
    compiler = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework/v4.0.30319/csc.exe"
    command = [str(compiler), "/nologo", "/target:exe", "/platform:x86", "/out:" + str(executable)]
    for filename in ("Elsinore.dll", "FSharp.Core.dll", "0Harmony.dll"):
        command.append("/reference:" + str(build / filename))
    command += [str(ROOT / "tools/patch/InvitedEventNotice.cs"), str(ROOT / "tools/patch/TestInvitedEventNotice.cs")]
    compiled = quiet_run(command)
    (build / "compile-output.txt").write_bytes(compiled.stdout + compiled.stderr)
    sys.path.insert(0, str(ROOT / "analysis"))
    from analyze import read_text_assets
    expected = {"schedule": "c9729c297f9df2d9442f9c899cb1fd2754ffe1af054ed24e385da837fa708f47",
                "names": "16e4bbcbb01d6769cb17429d756bed974e737b899cca57bd9501b0e6ded50489"}
    inputs = {}
    for name, digest, text in read_text_assets((managed.parent / "resources.assets").read_bytes()):
        if name in expected and digest == expected[name]:
            inputs[name] = build / (name + ".txt")
            inputs[name].write_bytes(text.encode("utf-8"))
    if set(inputs) != set(expected):
        raise RuntimeError("真实测试资源版本不匹配，禁止启动")
    result = run_compiled_test(compiled, executable, [inputs["schedule"], inputs["names"]])
    (build / "test-output.txt").write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError("真实格式器测试失败，进程已退出；诊断见 " + str(build))
    proof = json.loads(result.stdout.decode("utf-8-sig"))
    if not proof.get("passed") or not proof.get("real_formatter"):
        raise RuntimeError("真实格式器测试没有成功断言")
    proof["build_directory"] = str(build.relative_to(ROOT)).replace("\\", "/")
    proof["inherited_error_ui_suppression_checked"] = True
    proof["real_resource_sha256"] = expected
    proof["helper_sha256"] = hashlib.sha256((ROOT / "tools/patch/InvitedEventNotice.cs").read_bytes()).hexdigest()
    (ROOT / "runtime/build/invited-followup/formatter-result.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, ensure_ascii=False))


if __name__ == "__main__":
    main()
