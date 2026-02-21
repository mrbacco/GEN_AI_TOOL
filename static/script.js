function escapeHtml(text){
return String(text)
  .replaceAll("&","&amp;")
  .replaceAll("<","&lt;")
  .replaceAll(">","&gt;")
  .replaceAll('"',"&quot;")
  .replaceAll("'","&#39;")
}

function renderCompareTable(data){
const rows=Object.entries(data).map(([model,response])=>`
<tr>
<td class="model-cell">${escapeHtml(model)}</td>
<td class="response-cell">${escapeHtml(response ?? "")}</td>
</tr>
`).join("")

return `
<table class="results-table">
<thead>
<tr>
<th>Model</th>
<th>Response</th>
</tr>
</thead>
<tbody>${rows}</tbody>
</table>
`
}

async function send(){

const msg=document.getElementById("msg").value
const output=document.getElementById("output")
const model="gemini-1.5-flash"

const res=await fetch("/chat",{

method:"POST",

headers:{"Content-Type":"application/json"},

body:JSON.stringify({

message:msg,

model:model

})

})

const data=await res.json()

output.innerHTML=`
<table class="results-table">
<thead>
<tr><th>Model</th><th>Response</th></tr>
</thead>
<tbody>
<tr>
<td class="model-cell">${escapeHtml(model)}</td>
<td class="response-cell">${escapeHtml(data.response ?? "")}</td>
</tr>
</tbody>
</table>
`

}



async function compare(){
const output=document.getElementById("output")
const msg=document.getElementById("msg").value.trim()

if(!msg){
output.textContent="Please enter a message first."
return
}

try{
const res=await fetch("/compare",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({
message:msg,
models:["gemini-1.5-flash","gemini-1.5-flash-8b"]
})
})

let data
try{
data=await res.json()
}catch{
throw new Error(`Server returned ${res.status} ${res.statusText} and not JSON.`)
}

if(!res.ok){
throw new Error(data.error||`Request failed with status ${res.status}.`)
}

output.innerHTML=renderCompareTable(data)
}catch(err){
output.textContent=`Compare failed: ${err.message}`
}

}
