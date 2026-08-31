(function () {
    "use strict";

    var audio = document.getElementById("lectureAudio");

    /*
     * Seek lecture audio when a transcript timestamp
     * or topic timestamp is clicked.
     */
    function seekTo(seconds) {
        if (!audio) return;

        audio.currentTime = seconds;

        audio.play().catch(function (error) {
            console.error("Unable to play lecture audio:", error);
        });
    }


    document
        .querySelectorAll("[data-start-seconds]")
        .forEach(function (element) {

            element.addEventListener("click", function () {

                var seconds = parseFloat(
                    element.dataset.startSeconds
                );

                if (!isNaN(seconds)) {
                    seekTo(seconds);
                }

            });

        });


    /*
     * Transcript search
     */
    var transcriptSearch =
        document.getElementById("transcriptSearch");

    var transcriptTextEls =
        document.querySelectorAll(
            ".transcript-segment__text, .transcript-raw"
        );


    var originalTexts =
        Array.prototype.map.call(
            transcriptTextEls,
            function (element) {
                return element.textContent;
            }
        );


    function escapeRegExp(string) {

        return string.replace(
            /[.*+?^${}()|[\]\\]/g,
            "\\$&"
        );

    }


    function escapeHtml(string) {

        return string
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

    }


    function highlight(query) {

        transcriptTextEls.forEach(
            function (element, index) {

                var original =
                    originalTexts[index];

                if (!query) {

                    element.textContent =
                        original;

                    return;
                }

                var pattern =
                    new RegExp(
                        "(" +
                        escapeRegExp(query) +
                        ")",
                        "gi"
                    );

                var safeText =
                    escapeHtml(original);

                element.innerHTML =
                    safeText.replace(
                        pattern,
                        "<mark>$1</mark>"
                    );

            }
        );

    }


    if (transcriptSearch) {

        transcriptSearch.addEventListener(
            "input",
            function () {

                highlight(
                    transcriptSearch.value.trim()
                );

            }
        );

    }

})();