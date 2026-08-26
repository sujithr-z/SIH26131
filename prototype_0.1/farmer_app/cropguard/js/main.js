// ============================================================
// CropGuard — Diagnose page behaviour
// Handles: click-to-browse, drag & drop, image preview,
// and basic validation before the form is submitted to analyze.php
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
  var dropzone = document.getElementById('dropzone');
  var fileInput = document.getElementById('fileInput');
  var form = document.getElementById('analyzeForm');
  var analyzeBtn = document.getElementById('analyzeBtn');

  if (!dropzone || !fileInput || !form) return;

  // Clicking anywhere on the dashed box opens the native file picker
  dropzone.addEventListener('click', function () {
    fileInput.click();
  });

  // Drag styling
  ['dragenter', 'dragover'].forEach(function (evt) {
    dropzone.addEventListener(evt, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(function (evt) {
    dropzone.addEventListener(evt, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  // Actual drop -> put the file into the hidden <input type="file">
  // so it travels with the normal form submission (multipart/form-data)
  dropzone.addEventListener('drop', function (e) {
    var files = e.dataTransfer.files;
    if (files && files.length) {
      fileInput.files = files;
      showPreview(files[0]);
    }
  });

  // Manual browse via the hidden input
  fileInput.addEventListener('change', function () {
    if (fileInput.files && fileInput.files.length) {
      showPreview(fileInput.files[0]);
    }
  });

  function showPreview(file) {
    if (!file.type || file.type.indexOf('image/') !== 0) {
      alert('Please choose an image file (JPG, PNG, etc).');
      fileInput.value = '';
      return;
    }
    var reader = new FileReader();
    reader.onload = function (e) {
      dropzone.innerHTML =
        '<img src="' + e.target.result + '" class="preview-img" alt="Selected leaf photo">';
    };
    reader.readAsDataURL(file);
  }

  // Don't let the user hit Analyze with nothing selected
  form.addEventListener('submit', function (e) {
    if (!fileInput.files || !fileInput.files.length) {
      e.preventDefault();
      alert('Please take or upload a photo first.');
      return;
    }
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing…';
  });
});
