/*-----------------------------------------------------------------------------------

    Template Name: Carbook
 
    Note: This is Custom Js file

-----------------------------------------------------------------------------------

    [Table of contents]
    
    01. review-clint-swiper
    02. stickyHeader
    03. accordion-item
    04. Go to top
    05. loaded
    06. mousecursor
    07. stap
    08. wow
    09. reveal

-----------------------------------------------------------------------------------*/

if (typeof Swiper !== 'undefined') {

/* 01. review-clint-swiper */

   var swiper = new Swiper(".review-clint-swiper", {
    loop: true,
    speed: 1000,
    freeMode: true,
    slidesPerView: 1,
    spaceBetween: 0,
    autoplay: {
      delay: 2000,
    },
      pagination: {
        el: ".swiper-pagination",
        type: "fraction",
      },
      navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
      },
    }); 
   var swiper = new Swiper(".img-slider", {
    slidesPerView: 1,
    loop: true,
    speed: 1000,
    freeMode: true,
    grabCursor: true,
    effect: "fade",
    autoplay: {
      delay: 3000,
    }, 
  });
   var swiper = new Swiper(".vehiclemodels-slider", {
    slidesPerView: 1,
    loop: true,
    speed: 1000,
    freeMode: true, 
    grabCursor: false, // Disables grab cursor
  simulateTouch: false, // Disables mouse drag
  allowTouchMove: false, // Disables touch and mouse movement
  mousewheel: false, // Disables scrolling with the mouse wheel
    autoplay: {
      delay: 3000,
    }, 
     
    pagination: {
        el: ".swiper-pagination",
      },
  });
} 

 
/* 02. stickyHeader */

    if ($("#stickyHeader")[0]){
      var new_scroll_position = 0;

        var last_scroll_position;

        var header = document.getElementById("stickyHeader");



        window.addEventListener('scroll', function(e) {

        last_scroll_position = window.scrollY;



        // Scrolling down

        if (new_scroll_position < last_scroll_position && last_scroll_position > 100) {

          // header.removeClass('slideDown').addClass('slideUp');

          header.classList.remove("slideDown");

          header.classList.add("slideUp");



        // Scroll top

        } 

        else if (last_scroll_position < 100) {

          header.classList.remove("slideDown");

        } 

        else if (new_scroll_position > last_scroll_position) {

          header.classList.remove("slideUp");

          header.classList.add("slideDown");

        } 
          new_scroll_position = last_scroll_position;

        });

}
 
/* 03. accordion-item */

$('.accordion-item .heading').on('click', function(e) {
    e.preventDefault();

    if($(this).closest('.accordion-item').hasClass('active')) {
        $('.accordion-item').removeClass('active');
    } else {
        $('.accordion-item').removeClass('active');

        $(this).closest('.accordion-item').addClass('active');
    }
    var $content = $(this).next();
    $content.slideToggle(100);
    $('.accordion-item .content').not($content).slideUp('fast');
});

/* 04. Go to top */ 

function inVisible(element) { 
  var WindowTop = $(window).scrollTop();
  var WindowBottom = WindowTop + $(window).height();
  var ElementTop = element.offset().top;
  var ElementBottom = ElementTop + element.height();
  //animating the element if it is
  //visible in the viewport
  if ((ElementBottom <= WindowBottom) && ElementTop >= WindowTop)
    animate(element);
}

function animate(element) { 
  if (!element.hasClass('ms-animated')) {
    var maxval = element.data('max');
    var html = element.html();
    element.addClass("ms-animated");
    $({
      countNum: element.html()
    }).animate({
      countNum: maxval
    }, { 
      duration: 5000,
      easing: 'linear',
      step: function() {
        element.html(Math.floor(this.countNum) + html);
      },
      complete: function() {
        element.html(this.countNum + html);
      }
    });
  } 
} 
$(function() { 
  $(window).scroll(function() { 
    $("h3[data-max]").each(function() {
      inVisible($(this));
    });
  })
});
 

let calcScrollValue = () => {
  let scrollProgress = document.getElementById("progress");
  let progressValue = document.getElementById("progress-value");
  let pos = document.documentElement.scrollTop;
  let calcHeight =
    document.documentElement.scrollHeight -
    document.documentElement.clientHeight;
  let scrollValue = Math.round((pos * 100) / calcHeight);
  if (pos > 100) {
    scrollProgress.style.display = "grid";
  } else {
    scrollProgress.style.display = "none";
  }
  scrollProgress.addEventListener("click", () => {
    document.documentElement.scrollTop = 0;
  });
  scrollProgress.style.background = `conic-gradient(#000 ${scrollValue}%, #ffffff00 ${scrollValue}%)`;
};

window.onscroll = calcScrollValue;
window.onload = calcScrollValue;

/* 05. loaded */ 

$(window).on('load', function () {
    $("body").addClass("page-loaded");
    ("loaded")
});  
  
/* 06. mousecursor */

        function mousecursor() {
            if ($("body")) {
                const e = document.querySelector(".cursor-inner"),
                    t = document.querySelector(".cursor-outer");
                let n,
                    i = 0,
                    o = !1;
                (window.onmousemove = function(s) {
                    o ||
                        (t.style.transform =
                            "translate(" + s.clientX + "px, " + s.clientY + "px)"),
                        (e.style.transform =
                            "translate(" + s.clientX + "px, " + s.clientY + "px)"),
                        (n = s.clientY),
                        (i = s.clientX);
                }),
                $("body").on("mouseenter", "a, button , .cursor-pointer", function() {
                        e.classList.add("cursor-hover"), t.classList.add("cursor-hover");
                    }),
                    $("body").on("mouseleave", "a, button , .cursor-pointer", function() {
                        ($(this).is("a") && $(this).closest(".cursor-pointer").length) ||
                        (e.classList.remove("cursor-hover"),
                            t.classList.remove("cursor-hover"));
                    }),
                    (e.style.visibility = "visible"),
                    (t.style.visibility = "visible");
            }
        }
        $(function() {
            mousecursor();
        });

/* 07. stap */

        $(".stap").hover(function(){
              $(".stap").removeClass("active");
              $(this).addClass("active");
            }); 

/* 08. wow */

        new WOW().init();  

/* 09. reveal  */

        function reveal1() {
    var reveals = document.querySelectorAll(".reveal1");

    for (var i = 0; i < reveals.length; i++) {
      var windowHeight = window.innerHeight;
      var elementTop = reveals[i].getBoundingClientRect().top;
      var elementVisible = 150;
      if (elementTop < windowHeight - elementVisible) {
        reveals[i].classList.add("active");
      }
      //  else {
      //   reveals[i].classList.remove("active");
      // }
    }
  }
  window.addEventListener("scroll", reveal1);  

/* Brand filter button functionality */
document.addEventListener('DOMContentLoaded', function() {
    const brandButtons = document.querySelectorAll('.brand-filter-btn');
    const brandSearchForm = document.getElementById('brand-search-form');
    
    if (brandButtons.length > 0 && brandSearchForm) {
        brandButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                brandButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Get the brand from data attribute
                const selectedBrand = this.getAttribute('data-brand');
                
                // Wait for the dropdown to be populated, then set the value
                setTimeout(() => {
                    const makeSelect = brandSearchForm.querySelector('select[name="make"]');
                    if (makeSelect) {
                        // Try to find the option that matches the brand (case-insensitive)
                        let optionFound = false;
                        for (let i = 0; i < makeSelect.options.length; i++) {
                            if (makeSelect.options[i].value.toLowerCase() === selectedBrand.toLowerCase()) {
                                makeSelect.value = makeSelect.options[i].value;
                                optionFound = true;
                                break;
                            }
                        }
                        
                        if (optionFound) {
                            // Trigger change event to update models if needed
                            const event = new Event('change', { bubbles: true });
                            makeSelect.dispatchEvent(event);
                            
                            // Scroll to the form
                            brandSearchForm.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        } else {
                            console.warn(`Brand "${selectedBrand}" not found in dropdown`);
                        }
                    }
                }, 500); // Wait for API to populate dropdown
            });
        });
    }
});  