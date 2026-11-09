import type { Express } from "express";
import { createServer } from 'node:http';
import type { Server } from 'node:http';
import { spawn } from "node:child_process";
import path from "node:path";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  app.get("/api/status", (_req,res) => {
    res.json({
      platformAvailable: Boolean(process.env.OPENAI_API_KEY),
      groqAvailable: Boolean(process.env.GROQ_API_KEY || (process.env.CUSTOM_CRED_API_GROQ_COM_URL && process.env.CUSTOM_CRED_API_GROQ_COM_PROXY_AUTH_KEY) || (process.env.PROMOPROOF_GROQ_URL && process.env.PROMOPROOF_GROQ_TOKEN)),
      defaultModel: process.env.PROMOPROOF_MODEL || "gpt-5.4-mini",
      version: "1.0.0",
    });
  });
  let running = 0;
  const attempts = new Map<string,{since:number,count:number}>();
  app.post("/api/analyze", (req,res) => {
    const ip = req.ip || "unknown";
    const previous=attempts.get(ip);
    const bucket=previous && Date.now()-previous.since<1_800_000?previous:{since:Date.now(),count:0};
    if(bucket.count>=20)return res.status(429).json({error:"Prototype limit: 20 runs per 30 minutes. Use the local app for larger tests."});
    bucket.count++;attempts.set(ip,bucket);
    if (running >= 2) return res.status(429).json({error:"Two runs are active. Please try again shortly."});
    if (!Array.isArray(req.body.files) || !req.body.files.length) return res.status(400).json({error:"Upload screenplay files first."});
    if (!["platform","groq"].includes(req.body.provider || "platform")) return res.status(400).json({error:"Unknown provider."});
    running++;
    const worker=spawn("python", [path.join(process.cwd(),"engine.py")], {stdio:["pipe","pipe","pipe"]});
    let output="", closed=false;
    const finish=()=>{ if(!closed){closed=true;running--;clearTimeout(timer);} };
    const timer=setTimeout(()=>{worker.kill();finish();if(!res.headersSent)res.status(504).json({error:"Run exceeded ten minutes. Free-tier quotas may require a smaller pack or a later retry."});},600000);
    worker.stdout.on("data",(d)=>{output+=d.toString();if(output.length>12_000_000)worker.kill();});
    worker.stderr.on("data",()=>{}); // Do not persist source-containing exception payloads.
    worker.on("error",()=>{finish();if(!res.headersSent)res.status(500).json({error:"Analysis worker could not start."});});
    worker.on("close",(code)=>{
      finish();
      if(res.headersSent)return;
      try{const body=JSON.parse(output);res.status(code===0?200:400).json(body);}
      catch{res.status(500).json({error:"Analysis worker returned an invalid response."});}
    });
    res.on("close",()=>{if(!res.writableEnded){worker.kill();finish();}});
    worker.stdin.end(JSON.stringify(req.body));
  });

  return httpServer;
}
