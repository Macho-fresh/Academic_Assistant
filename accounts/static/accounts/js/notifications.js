function getCookie(name) {

    let cookieValue = null;

    if (
        document.cookie &&
        document.cookie !== ""
    ) {

        const cookies =
            document.cookie.split(";");

        for (
            let i = 0;
            i < cookies.length;
            i++
        ) {

            const cookie =
                cookies[i].trim();

            if (
                cookie.substring(
                    0,
                    name.length + 1
                ) === name + "="
            ) {

                cookieValue =
                    decodeURIComponent(
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


async function checkNotifications() {

    if (
        !("Notification" in window) ||
        Notification.permission !== "granted"
    ) {
        return;
    }

    try {

        const response = await fetch(
            "/notifications/unread/"
        );

        if (!response.ok) {
            return;
        }

        const data =
            await response.json();


        for (
            const item of data.notifications
        ) {

            const browserNotification =
                new Notification(
                    item.title,
                    {
                        body: item.message
                    }
                );


            browserNotification.onclick =
                function () {

                    window.focus();

                    window.location.href =
                        "/timetable/";

                    browserNotification.close();
                };


            await fetch(
                `/notifications/${item.id}/read/`,
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken":
                            getCookie(
                                "csrftoken"
                            )
                    }
                }
            );
        }

    } catch (error) {

        console.error(
            "Notification error:",
            error
        );
    }
}

checkNotifications();

setInterval(
    checkNotifications,
    30000
);