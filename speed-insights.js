/**
 * Vercel Speed Insights initialization
 * This script initializes Speed Insights for tracking web performance metrics
 */
(function() {
  // Initialize Speed Insights queue if not already present
  window.si = window.si || function() { 
    (window.siq = window.siq || []).push(arguments); 
  };
  
  // Inject the Speed Insights script
  function injectSpeedInsights() {
    // Check if we're in a browser environment
    if (typeof window === 'undefined') return;
    
    // Check if script is already injected
    const scriptSrc = '/_vercel/speed-insights/script.js';
    if (document.head.querySelector(`script[src="${scriptSrc}"]`)) return;
    
    // Create and inject the script
    const script = document.createElement('script');
    script.src = scriptSrc;
    script.defer = true;
    script.setAttribute('data-sdkn', '@vercel/speed-insights');
    script.setAttribute('data-sdkv', '1.3.1');
    
    // Add script to document head
    document.head.appendChild(script);
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectSpeedInsights);
  } else {
    injectSpeedInsights();
  }
})();
