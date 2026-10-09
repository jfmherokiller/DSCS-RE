"""Shared helpers for poking at the unpacked DSCS exe from Python (pefile + capstone)."""
import bisect
import re

import capstone
import pefile
from capstone import x86

EXE = r"E:\ReverseEngineProjects\CyberSleuth\bin\DigimonStoryCS.unpacked.exe"
B = 0x140000000

pe = pefile.PE(EXE)
img = pe.get_memory_mapped_image()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]])
funcs = sorted((e.struct.BeginAddress, e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
_starts = [b for b, _ in funcs]
rdata = [s for s in pe.sections if s.Name.startswith(b".rdata")][0]
RD_LO, RD_HI = rdata.VirtualAddress, rdata.VirtualAddress + rdata.Misc_VirtualSize


def cstr(rva):
    e = img.find(b"\0", rva)
    return img[rva:e].decode("latin1")


def func_of(va):
    i = bisect.bisect_right(_starts, va - B) - 1
    return funcs[i]


def rip_target(ins):
    for op in ins.operands:
        if op.type == x86.X86_OP_MEM and op.mem.base == x86.X86_REG_RIP:
            return ins.address + ins.size + op.mem.disp
    return None


def dis(lo, hi):
    """Disassemble [lo, hi) (VAs) with string annotations."""
    out = []
    for i in md.disasm(img[lo - B:hi - B], lo):
        t = rip_target(i)
        note = ""
        if t is not None:
            r = t - B
            note = f'  ; "{cstr(r)[:50]}"' if RD_LO <= r < RD_HI and cstr(r).isprintable() and cstr(r) else f"  ; {t:x}"
        out.append(f"{i.address:x} {i.mnemonic} {i.op_str}{note}")
    return "\n".join(out)


def find_strings(pattern):
    return {m.group().decode("latin1"): B + RD_LO + m.start()
            for m in re.finditer(pattern, img[RD_LO:RD_HI])}


def string_refs(targets):
    """targets: set of VAs -> {target: [(insn_va, func_start_va)]} over all .pdata functions."""
    refs = {}
    for b, e in funcs:
        for i in md.disasm(img[b:e], B + b):
            if i.disp_size == 4:
                t = rip_target(i)
                if t in targets:
                    refs.setdefault(t, []).append((i.address, B + b))
    return refs
