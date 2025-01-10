// Speech-on-hover functionality
(function() {
    // Check if the browser supports speech synthesis
    if (!('speechSynthesis' in window)) {
      console.error('Speech synthesis is not supported in this browser.');
      return;
    }
  
    // Initialize speech synthesis
    const synth = window.speechSynthesis;
    let isReaderEnabled = false;
    let currentUtterance = null;
  
    // Configure speech settings
    const speechConfig = {
      rate: 1,     // Speaking rate (0.1 to 10)
      pitch: 1,    // Voice pitch (0 to 2)
      volume: 1,   // Volume level (0 to 1)
      lang: 'en-US' // Language
    };
  
    // Function to read text content
    function readText(text) {
      if (!text || !text.trim()) return;
      
      // Stop any ongoing speech
      stopSpeaking();
      
      // Create and configure new utterance
      currentUtterance = new SpeechSynthesisUtterance(text);
      Object.assign(currentUtterance, speechConfig);
      
      // Start speaking
      synth.speak(currentUtterance);
    }
  
    // Function to stop speaking
    function stopSpeaking() {
      synth.cancel();
      currentUtterance = null;
    }
  
    // Toggle screen reader function
    function toggleScreenReader() {
      isReaderEnabled = !isReaderEnabled;
      stopSpeaking();
      
      // Show visual feedback
      const status = isReaderEnabled ? 'enabled' : 'disabled';
      const notification = document.createElement('div');
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        background: ${isReaderEnabled ? '#4CAF50' : '#f44336'};
        color: white;
        border-radius: 4px;
        z-index: 9999;
        transition: opacity 0.3s;
      `;
      notification.textContent = `Screen Reader ${status}`;
      document.body.appendChild(notification);
      
      // Remove notification after 2 seconds
      setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
      }, 2000);
    }
  
    // Get readable text from element
    function getElementText(element) {
      if (!element) return '';
      
      // Handle images
      if (element.tagName === 'IMG') {
        return element.alt || element.title || '';
      }
      
      // Handle inputs and buttons
      if (element.tagName === 'INPUT' || element.tagName === 'BUTTON') {
        return element.value || element.placeholder || element.textContent || '';
      }
      
      // Get direct text content only (excluding child elements)
      let text = Array.from(element.childNodes)
        .filter(node => node.nodeType === Node.TEXT_NODE)
        .map(node => node.textContent.trim())
        .join(' ')
        .trim();
      
      // If no direct text, try aria-label or title
      return text || element.getAttribute('aria-label') || element.title || '';
    }
  
    // Add hover listeners to element
    function addHoverListeners(element) {
      element.addEventListener('mouseenter', (e) => {
        if (!isReaderEnabled) return;
        
        const text = getElementText(element);
        if (text) {
          readText(text);
          e.stopPropagation();
        }
      });
  
      element.addEventListener('mouseleave', () => {
        if (isReaderEnabled) {
          stopSpeaking();
        }
      });
    }
  
    // Initialize functionality
    function init() {
      // Add keyboard shortcut listener
      document.addEventListener('keydown', (e) => {
        if (e.shiftKey && e.key.toLowerCase() === 'r') {
          toggleScreenReader();
        }
      });
  
      // Add hover listeners to all existing elements
      document.querySelectorAll('body *').forEach(addHoverListeners);
  
      // Observer for dynamic elements
      const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              addHoverListeners(node);
              node.querySelectorAll('*').forEach(addHoverListeners);
            }
          });
        });
      });
  
      // Start observing
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  
    // Start the initialization when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  })();