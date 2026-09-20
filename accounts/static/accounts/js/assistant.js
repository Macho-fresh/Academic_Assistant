const input = document.getElementById("assistantInput");
const sendButton = document.getElementById("sendButton");
const voiceButton = document.getElementById("voiceButton");
const chat = document.getElementById("assistantChat");

const clearChatButton =
    document.getElementById("clearChatButton");

clearChatButton.addEventListener(
    "click",
    async function () {

        const confirmed = confirm(
            "Clear your entire chat history?"
        );

        if (!confirmed) {
            return;
        }

        try {

            const response = await fetch(
                CLEAR_CHAT_URL,
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken":
                            getCookie("csrftoken")
                    }
                }
            );

            if (!response.ok) {
                throw new Error(
                    "Could not clear chat."
                );
            }

            chat.innerHTML = "";

            addMessage(
                "Ask me anything about your lectures.",
                "assistant"
            );

        } catch (error) {

            console.error(
                "CLEAR CHAT ERROR:",
                error
            );
        }
    }
);

document.addEventListener(
    "click",
    function (event) {

        const button = event.target.closest(
            ".assistant-speak-button"
        );

        if (!button) {
            return;
        }

        speakText(
            button.dataset.speech
        );
    }
);
// ==========================================
// CSRF TOKEN
// ==========================================

function getCookie(name) {

    let cookieValue = null;

    if (
        document.cookie &&
        document.cookie !== ""
    ) {

        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {

            cookie = cookie.trim();

            if (
                cookie.startsWith(
                    name + "="
                )
            ) {

                cookieValue = decodeURIComponent(
                    cookie.substring(
                        name.length + 1
                    )
                );

                break;
            }
        }
    }

    return cookieValue;
}


// ==========================================
// ADD MESSAGE TO CHAT
// ==========================================

function addMessage(
    text,
    role,
    options = {}
) {

    const messageWrapper =
        document.createElement("div");

    messageWrapper.classList.add(
        "assistant-message",
        role
    );


    const messageText =
        document.createElement("div");

    messageText.classList.add(
        "assistant-message-text"
    );

    messageText.textContent = text;

    messageWrapper.appendChild(
        messageText
    );


    // ======================================
    // LECTURE RESULT
    // ======================================

    if (
        options.lectureId
    ) {

        const resultBox =
            document.createElement("div");

        resultBox.classList.add(
            "assistant-result"
        );


        const lectureInfo =
            document.createElement("div");

        lectureInfo.classList.add(
            "assistant-result-info"
        );



        let lectureText = "";

        if (
            options.course
        ) {
            lectureText +=
                options.course + " • ";
        }

        if (
            options.lecture
        ) {
            lectureText +=
                options.lecture;
        }

        if (
            options.timestampDisplay
        ) {
            lectureText +=
                " • " +
                options.timestampDisplay;
        }


        lectureInfo.textContent =
            lectureText;


        const openLink =
            document.createElement("a");

        let lectureUrl =
            `/lecture-detail/${options.lectureId}`;

        if (
            options.timestamp !== null &&
            options.timestamp !== undefined
        ) {

            lectureUrl +=
                `?t=${options.timestamp}`;
        }

        openLink.href =
            lectureUrl;

        openLink.textContent =
            options.timestampDisplay
                ? "Open at timestamp"
                : "Open lecture";

        openLink.classList.add(
            "assistant-result-link"
        );


        resultBox.appendChild(
            lectureInfo
        );

        resultBox.appendChild(
            openLink
        );

        messageWrapper.appendChild(
            resultBox
        );
    }

    // ======================================
// TIMETABLE RESULT
// ======================================

    if (
        role === "assistant" &&
        options.matchType === "timetable"
    ) {

        const resultBox =
            document.createElement("div");

        resultBox.classList.add(
            "assistant-result"
        );


        const timetableLink =
            document.createElement("a");

        timetableLink.classList.add(
            "assistant-result-link"
        );

        timetableLink.href =
            "/timetable/";

        timetableLink.textContent =
            "View timetable";


        resultBox.appendChild(
            timetableLink
        );

        messageWrapper.appendChild(
            resultBox
        );
    }

    // ======================================
    // SPEAK BUTTON
    // ======================================

    if (
        role === "assistant" &&
        "speechSynthesis" in window
    ) {

        const speakButton =
            document.createElement("button");

        speakButton.type =
            "button";

        speakButton.classList.add(
            "assistant-speak-button"
        );

        speakButton.textContent =
            "Read aloud";

        speakButton.addEventListener(
            "click",
            function () {

                speakText(
                    text
                );
            }
        );

        messageWrapper.appendChild(
            speakButton
        );
    }


    chat.appendChild(
        messageWrapper
    );


    chat.scrollTop =
        chat.scrollHeight;
}


// ==========================================
// LOADING MESSAGE
// ==========================================

function addLoadingMessage() {

    const loading =
        document.createElement("div");

    loading.classList.add(
        "assistant-message",
        "assistant",
        "assistant-loading"
    );

    loading.id =
        "assistantLoading";

    loading.textContent =
        "Searching your lectures...";

    chat.appendChild(
        loading
    );

    chat.scrollTop =
        chat.scrollHeight;
}


function removeLoadingMessage() {

    const loading =
        document.getElementById(
            "assistantLoading"
        );

    if (loading) {
        loading.remove();
    }
}


// ==========================================
// SEND MESSAGE
// ==========================================

async function sendMessage() {

    const message =
        input.value.trim();

    if (!message) {
        return;
    }


    addMessage(
        message,
        "user"
    );


    input.value =
        "";

    sendButton.disabled =
        true;

    voiceButton.disabled =
        true;


    addLoadingMessage();


    try {

        const response =
            await fetch(
                ASK_ASSISTANT_URL,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "X-CSRFToken":
                            getCookie(
                                "csrftoken"
                            )
                    },

                    body:
                        JSON.stringify({
                            message: message
                        })
                }
            );


        const data =
            await response.json();


        removeLoadingMessage();


        if (!response.ok) {

            addMessage(
                data.error ||
                "Something went wrong.",
                "assistant"
            );

            return;
        }


        addMessage(
            data.answer,
            "assistant",
            {
                lecture:
                    data.lecture,

                course:
                    data.course,

                lectureId:
                    data.lecture_id,

                timestamp:
                    data.timestamp,

                timestampDisplay:
                    data.timestamp_display,
                
                matchType: data.match_type
            }
        );


    } catch (error) {

        removeLoadingMessage();

        console.error(
            error
        );

        addMessage(
            "Unable to contact the academic assistant.",
            "assistant"
        );


    } finally {

        sendButton.disabled =
            false;

        voiceButton.disabled =
            false;

        input.focus();
    }
}


// ==========================================
// SEND BUTTON
// ==========================================

sendButton.addEventListener(
    "click",
    sendMessage
);


// ==========================================
// ENTER KEY
// ==========================================

input.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    }
);


// ==========================================
// SPEECH RECOGNITION
// ==========================================

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


if (SpeechRecognition) {

    const recognition =
        new SpeechRecognition();


    recognition.lang =
        "en-US";

    recognition.continuous =
        false;

    recognition.interimResults =
        false;

    recognition.maxAlternatives =
        1;


    voiceButton.addEventListener(
        "click",
        function () {

            try {

                recognition.start();

                voiceButton.classList.add(
                    "listening"
                );

                voiceButton.disabled =
                    true;

                input.placeholder =
                    "Listening...";

            } catch (error) {

                console.error(
                    error
                );
            }
        }
    );


    recognition.onresult =
        function (event) {

            const transcript =
                event.results[0][0]
                    .transcript;


            input.value =
                transcript;


            voiceButton.classList.remove(
                "listening"
            );

            voiceButton.disabled =
                false;

            input.placeholder =
                "Ask about your lectures...";


            sendMessage();
        };


    recognition.onerror =
        function (event) {

            console.error(
                "Speech recognition error:",
                event.error
            );


            voiceButton.classList.remove(
                "listening"
            );

            voiceButton.disabled =
                false;

            input.placeholder =
                "Ask about your lectures...";


            let errorMessage =
                "I couldn't understand the voice command.";


            if (
                event.error ===
                "not-allowed"
            ) {

                errorMessage =
                    "Microphone permission was denied.";
            }


            if (
                event.error ===
                "no-speech"
            ) {

                errorMessage =
                    "I couldn't hear anything. Please try again.";
            }


            addMessage(
                errorMessage,
                "assistant"
            );
        };


    recognition.onend =
        function () {

            voiceButton.classList.remove(
                "listening"
            );

            voiceButton.disabled =
                false;

            input.placeholder =
                "Ask about your lectures...";
        };


} else {

    voiceButton.disabled =
        true;

    voiceButton.title =
        "Voice recognition is not supported in this browser.";
}


// ==========================================
// TEXT TO SPEECH
// ==========================================

function speakText(text) {

    if (
        !(
            "speechSynthesis"
            in window
        )
    ) {
        return;
    }


    window.speechSynthesis.cancel();


    const utterance =
        new SpeechSynthesisUtterance(
            text
        );


    utterance.rate =
        1;

    utterance.pitch =
        1;

    utterance.volume =
        1;


    window.speechSynthesis.speak(
        utterance
    );
}


// ==========================================
// STOP SPEECH WHEN PAGE CHANGES
// ==========================================

window.addEventListener(
    "beforeunload",
    function () {

        if (
            "speechSynthesis"
            in window
        ) {

            window
                .speechSynthesis
                .cancel();
        }
    }
);


// ==========================================
// SCROLL TO LATEST MESSAGE ON LOAD
// ==========================================

window.addEventListener(
    "load",
    function () {

        chat.scrollTop =
            chat.scrollHeight;

        input.focus();
    }
);