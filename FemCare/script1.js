// This script is for potential interactivity or analytics on clicks
document.querySelectorAll('.feature-box').forEach(box => {
    box.addEventListener('click', () => {
        console.log(`${box.querySelector('h3').textContent} clicked!`);
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const imageSection = document.querySelector('.image-section img');
    imageSection.addEventListener('click', () => {
      alert('Thank you for joining the conversation about periods!');
    });
  });
