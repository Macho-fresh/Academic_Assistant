(function () {
    "use strict";

    const editButton =
        document.getElementById("editProfileBtn");

    const cancelButton =
        document.getElementById("cancelEditBtn");

    const actions =
        document.getElementById("profileFormActions");

    const fullNameInput =
        document.getElementById("id_full_name");


    if (
        !editButton ||
        !fullNameInput ||
        !actions
    ) {
        return;
    }


    const originalName =
        fullNameInput.value;


    function enableEditing() {

        fullNameInput.removeAttribute(
            "readonly"
        );

        actions.hidden = false;

        editButton.hidden = true;

        fullNameInput.focus();

    }


    function cancelEditing() {

        fullNameInput.value =
            originalName;

        fullNameInput.setAttribute(
            "readonly",
            true
        );

        actions.hidden = true;

        editButton.hidden = false;

    }


    editButton.addEventListener(
        "click",
        enableEditing
    );


    if (cancelButton) {

        cancelButton.addEventListener(
            "click",
            cancelEditing
        );

    }

})();