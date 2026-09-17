console.log("AshuSeva JavaScript is working!");


const tokenForm = document.getElementById("tokenCheckForm");

if (tokenForm) {

    tokenForm.addEventListener("submit", function(event) {

        event.preventDefault();

        const tokenInput =
            document.getElementById("tokenNumber");

        let token =
            tokenInput.value.trim().toUpperCase();

        if (token === "") {
            return;
        }

        // Remove accidental spaces
        token = token.replace(/\s+/g, "");

        // Open the patient's queue page
        window.location.href = "/queue/" + token;

    });

}