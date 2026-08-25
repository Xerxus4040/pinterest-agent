import {open,seal} from "./crypto";
export const scopes="boards:read boards:write pins:read pins:write user_accounts:read";
export function authUrl(state:string){const u=new URL("https://www.pinterest.com/oauth/");u.searchParams.set("client_id",process.env.PINTEREST_CLIENT_ID!);u.searchParams.set("redirect_uri",process.env.PINTEREST_REDIRECT_URI!);u.searchParams.set("response_type","code");u.searchParams.set("scope",scopes);u.searchParams.set("state",state);return u.toString()}
async function tokenRequest(body:URLSearchParams){
 const basic=Buffer.from(`${process.env.PINTEREST_CLIENT_ID}:${process.env.PINTEREST_CLIENT_SECRET}`).toString("base64");
 const r=await fetch("https://api.pinterest.com/v5/oauth/token",{method:"POST",headers:{Authorization:`Basic ${basic}`,"Content-Type":"application/x-www-form-urlencoded"},body});
 if(!r.ok)throw new Error(`Pinterest token exchange failed: ${r.status} ${await r.text()}`);
 return r.json();
}
export async function exchange(code:string){
 const b=new URLSearchParams({grant_type:"authorization_code",code,redirect_uri:process.env.PINTEREST_REDIRECT_URI!,continuous_refresh:"true"});
 const t=await tokenRequest(b);
 return {accessToken:seal(t.access_token),refreshToken:t.refresh_token?seal(t.refresh_token):undefined,expiresAt:Date.now()+Number(t.expires_in||0)*1000}
}
export async function refresh(student:any){
 if(!student.pinterest?.refreshToken)throw new Error("No Pinterest refresh token");
 const b=new URLSearchParams({grant_type:"refresh_token",refresh_token:open(student.pinterest.refreshToken),continuous_refresh:"true"});
 const t=await tokenRequest(b);
 student.pinterest.accessToken=seal(t.access_token);
 if(t.refresh_token)student.pinterest.refreshToken=seal(t.refresh_token);
 student.pinterest.expiresAt=Date.now()+Number(t.expires_in||0)*1000;
 return student;
}
export async function pfetch(student:any,path:string,init:RequestInit={}){
 if(!student.pinterest?.accessToken)throw new Error("Pinterest is not connected");
 if(student.pinterest.expiresAt && student.pinterest.expiresAt<Date.now()+60000) await refresh(student);
 const token=open(student.pinterest.accessToken);
 const r=await fetch(`https://api.pinterest.com/v5${path}`,{...init,headers:{...(init.headers||{}),Authorization:`Bearer ${token}`,"Content-Type":"application/json"}});
 if(r.status===401 && student.pinterest.refreshToken){await refresh(student);const t=open(student.pinterest.accessToken);return fetch(`https://api.pinterest.com/v5${path}`,{...init,headers:{...(init.headers||{}),Authorization:`Bearer ${t}`,"Content-Type":"application/json"}})}
 return r;
}