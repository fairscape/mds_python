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

    $.validator.addMethod('strongPassword', function (value, element) {
        return this.optional(element)
            || value.length > 6
            && /\d/.test(value)
            && /[a-z]/i.test(value);
    }, 'Must contain at least 7 characters with 1 digit');

    //validate signup form on keyup and submit
    $("#form-signup").validate({
        rules: {
            firstName: {
                required: true,
                minlength: 3,
                lettersonly: true
            },
            lastName: {
                required: true,
                minlength: 3,
                lettersonly: true
            },
            email: {
                required: true,
                email: true
            },
            password1: {
                required: true,
                strongPassword: true
            },
            password2: {
                required: true,
                equalTo: "#password1"
            }
        },
        messages: {
            firstName: {
                required: "Please Enter your name",
                minlength: jQuery.validator.format("At least {0} characters required!")
            },
            lastName: {
                required: "Please Enter your name",
                minlength: jQuery.validator.format("At least {0} characters required!")
            },
            email: {
                required: "Please enter an email address",
                email: "Please enter a <em>valid</em> email address"
            },
            password1: {
                required: "Please enter a password"
            },
            password2: {
                required: "Please repeat password",
                equalTo: "Please enter the same password again"
            }
        },

        /** Enable to use use default fastapi form submit with @classmethod such as as_form(...)
            In fact without enabling the 2 lines below, jQuery validator does submit the form data automatically

            submitHandler: function (form) {
            form.submit();
        */

        // Enable the line below to submit form with custom Ajax request
        submitHandler: signupFormSubmitAjax

    });


    function signupFormSubmitAjax() {
        // serialize does not work
        //var data = $("#form-signin").serialize();
        $.ajax({
            type: 'POST',
            url: '/page/signup',
            // must mention contentType
            contentType: 'application/json',
            data: JSON.stringify({
                'firstName': firstName.value.trim(),
                'lastName': lastName.value.trim(),
                'email': email.value.trim(),
                'password1': password1.value.trim(),
                'password2': password2.value.trim(),
            }),
            beforeSend: function () {
                $("#info").fadeOut();
                $("#signupSubmit").html("Sending...")
            },
            success: function (response) {
                if (response.success == true) {
                    $("#signupSubmit").html("<img src='../../static/gif/Ajax-loader.gif' width='15'> &nbsp; Signing Up");
                    setTimeout('window.location.href = "/page/home"', 4000);
                }
                else {
                    $("#info").fadeIn(1000, function () {
                        $("#info").html("<div class='alert alert-danger'>" + response.message + "</div>");
                        $("#signupSubmit").html("Sign Up")
                    });
                }
            },
            error: function () {
                alert('Error Occurred!');
            }
        });
    }
});
