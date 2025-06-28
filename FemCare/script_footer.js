document.addEventListener('DOMContentLoaded', () => {
    // Select the form and its inputs
    const signUpForm = document.querySelector('.sign-up-form');

    // Check if the form exists
    if (!signUpForm) {
        console.error('Sign-up form not found!');
        return;
    }

    signUpForm.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent default form submission behavior

        // Get the input values
        const firstName = signUpForm.querySelector('input[placeholder="First Name"]').value.trim();
        const lastName = signUpForm.querySelector('input[placeholder="Last Name"]').value.trim();
        const email = signUpForm.querySelector('input[placeholder="Email Address"]').value.trim();

        // Validate the inputs
        if (!firstName || !lastName || !email) {
            alert('Please fill in all fields.');
            return;
        }

        // Display a success message
        alert(`Thank you, ${firstName} ${lastName}, for signing up! A confirmation email has been sent to ${email}.`);

        // Reset the form
        signUpForm.reset();
    });
});
