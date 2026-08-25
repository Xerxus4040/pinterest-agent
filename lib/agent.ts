import {ai,TEXT_MODEL,IMAGE_MODEL} from "./gemini";
import {put} from "@vercel/blob";
import {download,scanPublicFolder,Source} from "./drive";
import {Student,Approval,Store} from "./types";
import {pfetch} from "./pinterest";
import {log,saveStore} from "./store";

async function text(input:any){const r=await ai().models.generateContent({model:TEXT_MODEL,contents:input});return r.text||""}
export async function analyzeAndGenerate(student:Student,source:Source):Promise<Approval>{
 const {b,type}=await download(source.url);const base=b.toString("base64");
 const analysis=await text([{inlineData:{mimeType:type,data:base}},{text:`Analyze this architectural blueprint/sketch for Pinterest marketing. Return concise JSON with: product_type, rooms_or_features, style, audience, key_visual_details, marketing_angle. Do not invent dimensions.`}]);
 const seoRaw=await text(`Create Pinterest SEO for this product based on this AI analysis:\n${analysis}\nReturn JSON only with title (<=100 chars), description (<=800 chars), tags (10-15 keyword phrases), alt_text (<=500 chars). Avoid keyword stuffing.`);
 const seo=JSON.parse(seoRaw.replace(/```json|```/g,"").trim());
 const prompt=`Create a premium Pinterest marketing image from the provided blueprint. Preserve the real design intent and important layout/features; do not invent room counts or dimensions. Make it visually compelling, clean and professional for an architectural/home-plan Etsy audience. Vertical 2:3 composition. Include tasteful minimal headline text based only on this SEO title: "${seo.title}". Do not add fake prices, dimensions, guarantees, badges or logos.`;
 const interaction=await ai().interactions.create({model:IMAGE_MODEL,input:[{type:"image",mime_type:type,data:base},{type:"text",text:prompt}],response_format:{type:"image",aspect_ratio:"2:3",image_size:"1K"}});
 const out=interaction.output_image;if(!out)throw new Error("Gemini returned no image");
 const img=Buffer.from(out.data,"base64");
 const blob=await put(`generated/${student.id}/${Date.now()}.png`,img,{access:"public",contentType:"image/png"});
 return {id:crypto.randomUUID(),studentId:student.id,sourceId:source.id,sourceName:source.name,sourceUrl:source.url,imageUrl:blob.url,title:seo.title,description:seo.description,tags:seo.tags,createdAt:new Date().toISOString(),scheduledFor:new Date().toISOString(),status:"pending"};
}
export async function processStudent(store:Store,student:Student){
 if(!student.active)return;
 const sources=await scanPublicFolder(student.driveUrl);
 const next=sources.find(s=>!student.processedSourceIds.includes(s.id));
 if(!next){log(store,`${student.name}: no new source images`);return}
 const approval=await analyzeAndGenerate(student,next);
 student.processedSourceIds.push(next.id);student.lastRun=new Date().toISOString();
 if(student.mode==="auto"){approval.status="approved";store.approvals.unshift(approval);await publishApproval(store,approval)}
 else store.approvals.unshift(approval);
 log(store,`${student.name}: generated ${next.name}`);
 await saveStore(store);
}
export async function publishApproval(store:Store,a:Approval){
 const student=store.students.find(s=>s.id===a.studentId);if(!student)throw new Error("Student not found");
 if(!student.pinterest?.connected)throw new Error("Pinterest not connected");
 if(!student.boardId)throw new Error("No Pinterest board selected");
 const img=Buffer.from(await (await fetch(a.imageUrl)).arrayBuffer()).toString("base64");
 const body={title:a.title,description:`${a.description}\n\n${a.tags.map(x=>`#${x.replace(/\s+/g,"")}`).join(" ")}`,alt_text:a.description.slice(0,500),board_id:student.boardId,link:undefined,ai_disclosures:{values:["AI_MODIFIED"]},media_source:{source_type:"image_base64",content_type:"image/png",data:img,is_standard:true}};
 const r=await pfetch(student,"/pins",{method:"POST",body:JSON.stringify(body)});
 if(!r.ok)throw new Error(`Pinterest publish failed: ${r.status} ${await r.text()}`);
 const j=await r.json();a.status="published";a.pinId=j.id;log(store,`${student.name}: published ${a.title}`);await saveStore(store);
}