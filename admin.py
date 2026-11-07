#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Local, dependency-free metadata table. Run: uv run admin.py."""
from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import tempfile
import threading
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
METADATA = ROOT / "data" / "metadata.json"
FIELDS = ("public_title", "public_description", "real_title", "real_description", "date")
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()


def revision():
    return hashlib.sha256(METADATA.read_bytes() if METADATA.exists() else b"").hexdigest()


def read_metadata():
    if not METADATA.exists():
        return {}
    value = json.loads(METADATA.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("metadata.json 必须是 JSON 对象")
    return value


def snapshot():
    posts = ROOT / "content" / "posts"
    files = sorted(p.relative_to(posts).as_posix() for p in posts.rglob("*")
                   if p.is_file() and p.suffix.lower() in {".md", ".txt", ".markdown", ".mdown"}
                   and p.stem not in {"index", "_index"})
    with LOCK:
        return {"files": files, "metadata": read_metadata(), "revision": revision()}


def save_metadata(value, expected):
    if not isinstance(value, dict):
        raise ValueError("元数据必须是 JSON 对象")
    for filename, entry in value.items():
        if not isinstance(filename, str) or not isinstance(entry, dict):
            raise ValueError("每篇文章必须使用文件路径映射到元数据对象")
        for key in FIELDS:
            field = entry.get(key, "")
            if not isinstance(field, str):
                raise ValueError(f"{filename}: {key} 必须为文本")
            if key == "date" and field:
                if date.fromisoformat(field).isoformat() != field:
                    raise ValueError("日期必须使用 YYYY-MM-DD")
    with LOCK:
        if revision() != expected:
            raise FileExistsError("文件已被其他窗口或程序修改，请刷新后重新编辑。")
        METADATA.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=METADATA.parent,
                                             prefix=".metadata-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(value, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            temporary.replace(METADATA)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return revision()


HTML = r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>博客元数据</title><style>
body{font:15px/1.6 system-ui,sans-serif;color:#222;max-width:1500px;margin:32px auto;padding:0 20px}
h1{font-size:24px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}
th{white-space:nowrap}input,textarea{box-sizing:border-box;min-width:160px;width:100%;font:inherit;padding:6px;border:1px solid #bbb}
textarea{min-height:76px;resize:vertical}button{font:inherit;background:white;border:1px solid #555;padding:6px 18px;cursor:pointer}
.scroll{overflow:auto}#status{min-height:1.6em}td:first-child{min-width:160px;overflow-wrap:anywhere}
</style><h1>博客元数据</h1><p>文件名相对于 content/posts/。留空即使用默认值；公开字段不会从真实字段取值。日期使用 YYYY-MM-DD。</p>
<button id="save" disabled>保存</button> <span id="status" role="status">正在读取…</span>
<div class="scroll"><table><thead><tr><th>文件</th><th>公开标题</th><th>公开简介</th><th>真实标题</th><th>真实简介</th><th>日期</th></tr></thead><tbody id="rows"></tbody></table></div>
<script>
const fields=['public_title','public_description','real_title','real_description','date'];
let metadata={}, revision='', dirty=false;
const save=document.querySelector('#save'), status=document.querySelector('#status');
const token=location.hash.slice(1);
async function request(path,options={}){
  const response=await fetch(path,{...options,headers:{'Content-Type':'application/json','X-Admin-Token':token}});
  const result=await response.json(); if(!response.ok) throw Error(result.error); return result;
}
request('/api/metadata').then(data=>{
  metadata=data.metadata; revision=data.revision;
  for(const file of data.files){
    const row=document.createElement('tr'), name=document.createElement('td'); name.textContent=file;row.append(name);
    for(const field of fields){
      const cell=document.createElement('td'), input=document.createElement(field.endsWith('description')?'textarea':'input');
      input.value=typeof metadata[file]?.[field]==='string'?metadata[file][field]:'';
      input.setAttribute('aria-label',file+' '+field);
      if(field==='date'){input.type='date';}
      input.addEventListener('input',()=>{dirty=true;status.textContent='有未保存的修改';});
      input.dataset.field=field;cell.append(input);row.append(cell);
    }
    row.dataset.file=file;document.querySelector('#rows').append(row);
  }
  save.disabled=false; status.textContent=`已读取 ${data.files.length} 篇文章`;
}).catch(error=>{status.textContent=error.message;});
save.addEventListener('click',async()=>{
  save.disabled=true;
  try{
    const next=structuredClone(metadata);
    for(const row of document.querySelectorAll('#rows tr')){
      const file=row.dataset.file;
      const entry=next[file] && typeof next[file]==='object' && !Array.isArray(next[file])?next[file]:{};
      for(const input of row.querySelectorAll('input,textarea')){
        if(!input.checkValidity()) throw Error(file+'：日期格式无效');
        const value=input.value.trim();if(value) entry[input.dataset.field]=value;else delete entry[input.dataset.field];
      }
      if(Object.keys(entry).length) next[file]=entry;else delete next[file];
    }
    const result=await request('/api/metadata',{method:'POST',body:JSON.stringify({metadata:next,revision})});
    metadata=next;revision=result.revision;dirty=false;status.textContent='已保存到 data/metadata.json';
  }catch(error){status.textContent=error.message;}finally{save.disabled=false;}
});
window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
</script></html>'''


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, value, content_type="application/json; charset=utf-8"):
        body = value.encode("utf-8") if isinstance(value, str) else json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        origin = self.headers.get("Origin")
        expected = f"http://127.0.0.1:{self.server.server_port}"
        return (self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"
                and (origin is None or origin == expected)
                and secrets.compare_digest(self.headers.get("X-Admin-Token", ""), TOKEN))

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self.reply(200, HTML, "text/html; charset=utf-8")
        elif path == "/api/metadata":
            if not self.authorized():
                return self.reply(403, {"error": "请从启动脚本给出的完整地址进入。"})
            try:
                self.reply(200, snapshot())
            except (OSError, ValueError) as error:
                self.reply(400, {"error": str(error)})
        else:
            self.reply(404, {"error": "Not found"})

    def do_POST(self):
        if urlsplit(self.path).path != "/api/metadata":
            return self.reply(404, {"error": "Not found"})
        if not self.authorized():
            return self.reply(403, {"error": "无效的本地会话。"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2_000_000:
                raise ValueError("请求大小无效")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("请求必须为 JSON 对象")
            result = save_metadata(data.get("metadata"), data.get("revision"))
            self.reply(200, {"revision": result})
        except FileExistsError as error:
            self.reply(409, {"error": str(error)})
        except (OSError, ValueError) as error:
            self.reply(400, {"error": str(error)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=0, help="本地端口，默认自动选择")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        url = f"http://127.0.0.1:{server.server_port}/#{TOKEN}"
        print(f"元数据管理：{url}\n按 Ctrl+C 退出。", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
