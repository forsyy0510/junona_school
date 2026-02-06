// Бургер-меню
const burger = document.querySelector('.burger');
const navInner = document.querySelector('.nav-inner');
if (burger && navInner) {
    burger.addEventListener('click', () => {
        navInner.classList.toggle('open');
    });
}

// Плавное появление карточек при скролле
function revealOnScroll() {
    const cards = document.querySelectorAll('.card, .item');
    const windowHeight = window.innerHeight;
    cards.forEach(card => {
        const rect = card.getBoundingClientRect();
        if (rect.top < windowHeight - 60) {
            card.style.opacity = 1;
            card.style.transform = 'none';
        } else {
            card.style.opacity = 0;
            card.style.transform = 'translateY(40px)';
        }
    });
}
window.addEventListener('scroll', revealOnScroll);
window.addEventListener('DOMContentLoaded', revealOnScroll);

document.addEventListener('DOMContentLoaded', function() {
  var btnShow = document.getElementById('sidebarMenuMoreBtn');
  var btnHide = document.getElementById('sidebarMenuHideBtn');
  var more = document.getElementById('sidebarMenuMore');
  if (btnShow && btnHide && more) {
    btnShow.addEventListener('click', function() {
      more.style.display = 'block';
      btnShow.style.display = 'none';
      btnShow.setAttribute('aria-expanded', 'true');
    });
    btnHide.addEventListener('click', function() {
      more.style.display = 'none';
      btnShow.style.display = 'block';
      btnShow.setAttribute('aria-expanded', 'false');
    });
  }
  // Слайдер объявлений
  var scroll = document.querySelector('.announcements-scroll');
  var btnLeft = document.querySelector('.slider-btn--left');
  var btnRight = document.querySelector('.slider-btn--right');
  if (scroll && btnLeft && btnRight) {
    btnLeft.addEventListener('click', function() {
      scroll.scrollBy({ left: -260 - 24, behavior: 'smooth' });
    });
    btnRight.addEventListener('click', function() {
      scroll.scrollBy({ left: 260 + 24, behavior: 'smooth' });
    });
  }

  // Слайдер изображений в новостях
  setTimeout(function() {
    var galleryContainer = document.querySelector('.image-gallery');
  
  if (galleryContainer) {
    var slides = galleryContainer.querySelectorAll('.slider-slide');
    var prevBtn = galleryContainer.querySelector('.gallery-prev');
    var nextBtn = galleryContainer.querySelector('.gallery-next');
    var dots = galleryContainer.querySelectorAll('.gallery-dot');
    var currentSlide = 0;

    function showSlide(index) {
      slides.forEach((slide, i) => {
        slide.style.display = i === index ? 'flex' : 'none';
      });
      dots.forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
      });
    }

    function nextSlide() {
      currentSlide = (currentSlide + 1) % slides.length;
      showSlide(currentSlide);
    }

    function prevSlide() {
      currentSlide = (currentSlide - 1 + slides.length) % slides.length;
      showSlide(currentSlide);
    }

    if (slides.length > 1) {
      // Показываем только первое изображение изначально
      showSlide(0);

      if (prevBtn) {
        prevBtn.addEventListener('click', prevSlide);
      }
      if (nextBtn) {
        nextBtn.addEventListener('click', nextSlide);
      }

      dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
          currentSlide = index;
          showSlide(currentSlide);
        });
      });
    } else if (slides.length === 1) {
      showSlide(0);
    }
  }
  }, 100); // Задержка 100мс
}); 