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
        submitHandler: signinFormSubmitAjax

    });

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

});
