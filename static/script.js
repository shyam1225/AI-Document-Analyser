let isProcessing= false;
const questionInput = document.getElementById("questionInput");

questionInput.addEventListener("input", () => {

    if(questionInput.value.trim() !== ""){
        document.getElementById("sampleQuestions")
                .style.display = "none";
    }

});
const uploadSection =document.querySelector(".upload-section");
const chatContainer =document.getElementById("chatContainer");
chatContainer.addEventListener("scroll", () => {

    if(chatContainer.scrollTop > 50){
        uploadSection.classList.add("hidden");
    }
    else{
        uploadSection.classList.remove("hidden");
    }

});
const uploadBtn = document.getElementById("uploadBtn");
const pdfFile = document.getElementById("pdfFile");
const fileInfo = document.getElementById("fileInfo");
uploadBtn.addEventListener("click", () => {
    pdfFile.click();
});
pdfFile.addEventListener("change", () => {
    if (pdfFile.files.length > 0) {
        fileInfo.textContent = `${pdfFile.files.length} file(s) selected`;
    } else {
        fileInfo.textContent =
            "supported formats: pdf, txt, docx, png, jpg, jpeg";
    }
});
let uploadComplete = false;
const sendBtn = document.getElementById("sendBtn");
const files = document.getElementById("pdfFile");
files.multiple = true;
const preview = document.getElementById("preview");
preview.innerHTML = "";
async function useQuestion(question){

    document.getElementById("sampleQuestions")
            .style.display = "none";

    document.getElementById("questionInput").value =
            question;

    await sendQuestion();
}
files.addEventListener("change", async function(event) {
    
    const loader = document.getElementById("load");
    loader.style.display = "flex"; // SHOW LOADER

    try {
        const uploadData = new FormData();
        preview.innerHTML = "";
        sendBtn.disabled = true;
        sendBtn.textContent = "Processing...";
        uploadComplete = false;

        for (const file of event.target.files) {
            const fileURL = URL.createObjectURL(file);
            preview.innerHTML += `
                <a href="${fileURL}" target="_blank">
                    ${file.name}
                </a><br>
            `;

            uploadData.append("files", file);
        }

        const response = await fetch("/upload", {
            method: "POST",
            body: uploadData
        });

        const data = await response.json();
        console.log(data);
        uploadComplete = true;
        document.getElementById("sampleQuestions")
        .style.display = "flex";
    }
    catch(error) {
        console.error(error);
    }
    finally {
        loader.style.display = "none"; // HIDE LOADER
        sendBtn.disabled = false;
        sendBtn.textContent = "Send";
    }
});


function addBotMessage(message){

    const chatContainer =
        document.getElementById("chatContainer");

    chatContainer.innerHTML += `
        <div class="bot-message">
            ${message}
        </div>
    `;

    chatContainer.scrollTop =
        chatContainer.scrollHeight;
}

async function sendQuestion() {

    if (isProcessing) return;

    isProcessing = true;

    const questionInput = document.getElementById("questionInput");
    const sendBtn = document.querySelector(".send-btn");
    const chatContainer = document.getElementById("chatContainer");

    sendBtn.disabled = true;
    questionInput.disabled = true;

    try {

        const question = questionInput.value.trim();

        if (!uploadComplete) {
            thinkingDiv.innerHTML = "Please wait until document processing is complete.";
            return;
        }

        if (question === "") {
            return;
        }

        // User message
        chatContainer.innerHTML += `
            <div class="message">
                ${question}
            </div>
        `;

        // Thinking message
        const thinkingDiv = document.createElement("div");
        thinkingDiv.className = "bot-message";
        thinkingDiv.innerHTML = "Thinking...";

        chatContainer.appendChild(thinkingDiv);

        chatContainer.scrollTop =
            chatContainer.scrollHeight;

        const formData = new FormData();
        formData.append("question", question);

        questionInput.value = "";

        console.log("Sending request...");

        const response = await fetch("/ask", {
            method: "POST",
            body: formData
        });

        console.log("Response received");

        const data = await response.json();

        try {

            const jsonMatch =
                data.answer.match(/\{[\s\S]*\}/);

            if (!jsonMatch) {
                throw new Error("No JSON found");
            }

            const chartData =
                JSON.parse(jsonMatch[0]);

            console.log(chartData);

            if (chartData.type === "chart") {

                thinkingDiv.innerHTML = "";

                const chartWrapper =
                    document.createElement("div");

                chartWrapper.style.width = "600px";
                chartWrapper.style.maxWidth = "100%";
                chartWrapper.style.height = "350px";
                chartWrapper.style.background = "#ffffff";
                chartWrapper.style.borderRadius = "12px";
                chartWrapper.style.padding = "15px";

                const canvas =
                    document.createElement("canvas");

                chartWrapper.appendChild(canvas);
                thinkingDiv.appendChild(chartWrapper);

                let datasetConfig = {};

                switch (chartData.chart_type) {

                    case "line":
                        datasetConfig = {
                            label: chartData.title,
                            data: chartData.values,
                            borderColor: "#3b82f6",
                            backgroundColor:
                                "rgba(59,130,246,0.2)",
                            fill: true,
                            tension: 0.4,
                            pointRadius: 5
                        };
                        break;

                    case "bar":
                        datasetConfig = {
                            label: chartData.title,
                            data: chartData.values,
                            backgroundColor: [
                                "#3b82f6",
                                "#8b5cf6",
                                "#10b981",
                                "#f59e0b",
                                "#ef4444",
                                "#06b6d4"
                            ]
                        };
                        break;

                    case "pie":
                    case "doughnut":
                        datasetConfig = {
                            label: chartData.title,
                            data: chartData.values,
                            backgroundColor: [
                                "#3b82f6",
                                "#8b5cf6",
                                "#10b981",
                                "#f59e0b",
                                "#ef4444",
                                "#06b6d4",
                                "#ec4899",
                                "#14b8a6"
                            ]
                        };
                        break;

                    default:
                        datasetConfig = {
                            label: chartData.title,
                            data: chartData.values,
                            borderColor: "#3b82f6"
                        };
                }

                new Chart(canvas, {
                    type: chartData.chart_type,
                    data: {
                        labels: chartData.labels,
                        datasets: [datasetConfig]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,

                        plugins: {
                            title: {
                                display: true,
                                text: chartData.title,
                                color: "#111827",
                                font: {
                                    size: 18
                                }
                            },

                            legend: {
                                labels: {
                                    color: "#111827"
                                }
                            }
                        },

                        scales:
                            chartData.chart_type === "pie" ||
                            chartData.chart_type === "doughnut"
                                ? {}
                                : {
                                      x: {
                                          ticks: {
                                              color: "#111827"
                                          }
                                      },
                                      y: {
                                          ticks: {
                                              color: "#111827"
                                          }
                                      }
                                  }
                    }
                });

            } else {

                thinkingDiv.innerHTML =
                    marked.parse(data.answer);
            }

        } catch (error) {

            console.log("Not chart JSON:", error);

            thinkingDiv.innerHTML =
                marked.parse(data.answer);
        }

        chatContainer.scrollTop =
            chatContainer.scrollHeight;

    } catch (error) {

        console.error("Error:", error);

        const errorDiv =
            document.createElement("div");

        errorDiv.className = "bot-message";
        errorDiv.innerHTML =
            "An error occurred while processing your request.";

        chatContainer.appendChild(errorDiv);

    } finally {

        sendBtn.disabled = false;
        questionInput.disabled = false;
        isProcessing = false;
    }
}