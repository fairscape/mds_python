$(function () {

    $.validator.setDefaults({
        errorClass: 'invalid-feedback',
        highlight: function (element) {
            $(element).addClass('is-invalid');
        },
        unhighlight: function (element) {
            $(element).removeClass('is-invalid');
            $(element).addClass('is-valid');
        }
    });

    //validate signin form on keyup and submit
    $("#form-signin").validate({
        rules: {
            email: {
                required: true,
                email: true
            },
            password: {
                required: true,
                nowhitespace: true,
                minlength: 5
            }
        },
        messages: {
            email: {
                required: "Please enter an email address",
                email: "Please enter a <em>valid</em> email address"
            },
            password: {
                required: "Please enter a password",
                minlength: jQuery.validator.format("At least {0} characters required!")
            }
        },


        /** Enable to use use default fastapi form submit with @classmethod such as as_form(...)
            In fact without enable the 2 lines below, jQuery validator does submit the form data automatically

            submitHandler: function (form) {
            form.submit();
        */

        // Enable the line below to submit form with custom Ajax request
        // submitHandler: signinFormSubmitAjax
        submitHandler: signinFormSubmit

    });

    function signinFormSubmit() {
        var form= $("#form-signin");

        // Using the core $.ajax() method
        $.ajax({

            // The URL for the request
            url: "/login",

            // The data to send (will be converted to a query string)
            /*
            data: JSON.stringify({
                'email': email.value.trim(),
                'password': password.value.trim()
            }),
            */
            data: form.serialize(),

            // Whether this is a POST or GET request
            type: "POST",

            // The type of data we expect back
            dataType: "json",
        })
            // Code to run if the request succeeds (is done);
            // The response is passed to the function
            .done(function (response, textStatus, xhr) {
                console.log(response.session);
                console.log(textStatus);
                console.log(xhr);

                if (textStatus === "success") {
                    $("#signinSubmit").html("<img src='../../static/gif/Ajax-loader.gif' width='15'> &nbsp; Signing In");
                    setTimeout('window.location.href = "/page/home"', 4000);
                }
                else {
                    $("#info").fadeIn(1000, function () {
                        $("#info").html("<div class='alert alert-danger'>" + response.content + "</div>");
                        $("#signinSubmit").html("Sign In")
                    });
                }
            })
            // Code to run if the request fails; the raw request and
            // status codes are passed to the function
            .fail(function (xhr, status, errorThrown) {
                alert("Sorry, there was a problem!");
                console.log("Error: " + errorThrown);
                console.log("Status: " + status);
                console.dir(xhr);
                if (xhr.status === 401 || xhr.statusText === "Unauthorized") {
                    console.log(xhr.responseText);
                    console.log(xhr.responseJSON['error']);
                    $("#info").fadeIn(1000, function () {
                        $("#info").html("<div class='alert alert-danger'>" + xhr.responseJSON['error'] + "</div>");
                        $("#signinSubmit").html("Sign In")
                    });
                }
            })
            // Code to run regardless of success or failure;
            .always(function (xhr, status) {
                alert("The request is complete!");
            });
    }


    /*
    function signinFormSubmitAjax() {
        // serialize does not work
        // var data = $("#form-signin").serialize();
        $.ajax({
            type: 'POST',
            url: '/page/signin',
            // must mention contentType
            contentType: 'application/json',
            data: JSON.stringify({
                'email': email.value.trim(),
                'password': password.value.trim()
            }),
            beforeSend: function () {
                $("#info").fadeOut();
                $("#signinSubmit").html("Sending...")
            },
            success: function (response) {
                if (response.success == true) {
                    $("#signinSubmit").html("<img src='../../static/gif/Ajax-loader.gif' width='15'> &nbsp; Signing In");
                    setTimeout('window.location.href = "/page/home"', 4000);
                }
                else {
                    $("#info").fadeIn(1000, function () {
                        $("#info").html("<div class='alert alert-danger'>" + response.message + "</div>");
                        $("#signinSubmit").html("Sign In")
                    });
                }
            },
            error: function () {
                alert('Error Occurred! Contact Support.');
            }
        });

    }
    */

});
