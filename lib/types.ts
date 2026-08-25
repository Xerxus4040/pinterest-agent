export type Student={
 id:string; name:string; driveUrl:string; active:boolean;
 pinterest?:{connected:boolean;username?:string;accessToken?:string;refreshToken?:string;expiresAt?:number};
 boardId?:string; boardName?:string;
 mode:"approval"|"auto"; postsPerDay:number; postHour:number; timezone:string;
 processedSourceIds:string[];
 lastRun?:string; createdAt:string;
};
export type Approval={
 id:string; studentId:string; sourceId:string; sourceName:string; sourceUrl:string;
 imageUrl:string; title:string; description:string; tags:string[];
 createdAt:string; scheduledFor:string; status:"pending"|"approved"|"rejected"|"published"|"failed";
 error?:string; pinId?:string;
};
export type Store={students:Student[];approvals:Approval[];logs:{at:string;message:string;ok:boolean}[]};