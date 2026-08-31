const lectureAudio = document.getElementById("lectureAudio");


function jumpToTimestamp(seconds) {

    if (!lectureAudio) {
        console.error("Audio player not found.");
        return;
    }

    seconds = parseFloat(seconds);

    if (isNaN(seconds)) {
        console.error("Invalid timestamp.");
        return;
    }

    console.log("Trying to seek to:", seconds);

    lectureAudio.pause();


    function doSeek() {

        console.log(
            "Duration:",
            lectureAudio.duration
        );

        console.log(
            "Seekable ranges:",
            lectureAudio.seekable.length
        );


        if (lectureAudio.seekable.length > 0) {

            console.log(
                "Seekable start:",
                lectureAudio.seekable.start(0)
            );

            console.log(
                "Seekable end:",
                lectureAudio.seekable.end(
                    lectureAudio.seekable.length - 1
                )
            );
        }


        /*
         * Use fastSeek when supported.
         */
        if (
            typeof lectureAudio.fastSeek === "function"
        ) {

            lectureAudio.fastSeek(seconds);

        } else {

            lectureAudio.currentTime = seconds;

        }


        console.log(
            "currentTime after seek:",
            lectureAudio.currentTime
        );
    }


    if (lectureAudio.readyState >= 1) {

        doSeek();

    } else {

        lectureAudio.addEventListener(
            "loadedmetadata",
            doSeek,
            { once: true }
        );
    }

}


/*
 * Wait until browser confirms seeking
 * before playing.
 */
lectureAudio.addEventListener(
    "seeked",
    function () {

        console.log(
            "Seek completed:",
            lectureAudio.currentTime
        );

        lectureAudio.play()
            .catch(function (error) {
                console.error(
                    "Playback error:",
                    error
                );
            });

    }
);


document.addEventListener(
    "click",
    function (event) {

        const element =
            event.target.closest(
                "[data-start-seconds]"
            );

        if (!element) {
            return;
        }

        event.preventDefault();

        const seconds =
            element.dataset.startSeconds;

        console.log(
            "Jumping to:",
            seconds,
            "seconds"
        );

        jumpToTimestamp(seconds);

    }
);