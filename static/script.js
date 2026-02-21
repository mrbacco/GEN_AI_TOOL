const chat = document.getElementById("chat")
const input = document.getElementById("msg")
const fileInput = document.getElementById("file")


// ========================
// ADD MESSAGE
// ========================

function addMessage(text, sender) {

    const div = document.createElement("div")

    div.className = "message " + sender

    div.innerText = text

    chat.appendChild(div)

    chat.scrollTop = chat.scrollHeight

    return div
}


// ========================
// SEND MESSAGE
// ========================

async function send(){

    const text = input.value.trim()

    if(!text) return

    addMessage(text, "user")

    input.value = ""

    const botDiv = addMessage("", "bot")

    try{

        const res = await fetch("/chat", {

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                message:text,
                model:"mistral"
            })
        })


        if(res.status === 404){

            botDiv.innerText = "ERROR: /chat endpoint not found"

            return
        }


        const reader = res.body.getReader()

        const decoder = new TextDecoder()


        while(true){

            const {done,value} = await reader.read()

            if(done) break

            botDiv.innerText += decoder.decode(value)

            chat.scrollTop = chat.scrollHeight
        }

    }
    catch(err){

        botDiv.innerText = "Connection error"

        console.error(err)
    }
}


// ========================
// FILE UPLOAD
// ========================

fileInput?.addEventListener("change", async function () {

    const file = fileInput.files[0]

    if (!file) return

    addMessage("Uploading: " + file.name, "user")

    const botDiv = addMessage("", "bot")

    try {

        const response = await fetch("/upload", {

            method: "POST",

            body: new FormData().append("file", file)

        })

        if(response.status === 404){

            botDiv.innerText = "ERROR: /upload not found"

            return
        }

        botDiv.innerText = "File processed"

    }
    catch {

        botDiv.innerText = "Upload failed"

    }

})


// ========================
// ENTER SUPPORT
// ========================

input?.addEventListener("keydown", function (event) {

    if (event.key === "Enter") {

        send()

    }

})