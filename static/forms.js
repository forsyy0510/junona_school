// Модуль для работы с формами
class FormManager {
    constructor() {
        this.forms = new Map();
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeForms();
        });
    }

    initializeForms() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            this.registerForm(form);
        });
    }

    registerForm(form) {
        const formId = form.id || 'form_' + Date.now();
        form.id = formId;
        
        const formData = {
            element: form,
            id: formId,
            fields: new Map(),
            validation: {},
            submitHandler: null
        };
        
        this.forms.set(formId, formData);
        this.initializeFormFields(form);
        this.setupFormValidation(form);
    }

    initializeFormFields(form) {
        const formData = this.forms.get(form.id);
        if (!formData) return;
        
        const fields = form.querySelectorAll('input, textarea, select');
        fields.forEach(field => {
            this.registerField(form, field);
        });
    }

    registerField(form, field) {
        const formData = this.forms.get(form.id);
        if (!formData) return;
        
        const fieldData = {
            element: field,
            name: field.name,
            type: field.type,
            required: field.hasAttribute('required'),
            validation: this.getFieldValidation(field),
            value: field.value
        };
        
        formData.fields.set(field.name, fieldData);
        
        // Добавляем обработчики событий
        field.addEventListener('input', () => this.handleFieldChange(form, field));
        field.addEventListener('blur', () => this.validateField(form, field));
        field.addEventListener('focus', () => this.clearFieldError(field));
    }

    getFieldValidation(field) {
        const validation = {};
        
        if (field.hasAttribute('required')) {
            validation.required = true;
        }
        
        if (field.type === 'email') {
            validation.email = true;
        }
        
        if (field.type === 'url') {
            validation.url = true;
        }
        
        if (field.hasAttribute('minlength')) {
            validation.minLength = parseInt(field.getAttribute('minlength'));
        }
        
        if (field.hasAttribute('maxlength')) {
            validation.maxLength = parseInt(field.getAttribute('maxlength'));
        }
        
        if (field.hasAttribute('pattern')) {
            validation.pattern = field.getAttribute('pattern');
        }
        
        return validation;
    }

    handleFieldChange(form, field) {
        const formData = this.forms.get(form.id);
        if (!formData) return;
        
        const fieldData = formData.fields.get(field.name);
        if (fieldData) {
            fieldData.value = field.value;
        }
    }

    validateField(form, field) {
        const formData = this.forms.get(form.id);
        if (!formData) return true;
        
        const fieldData = formData.fields.get(field.name);
        if (!fieldData) return true;
        
        const value = field.value.trim();
        const validation = fieldData.validation;
        let isValid = true;
        let errorMessage = '';
        
        // Проверка обязательности
        if (validation.required && !value) {
            isValid = false;
            errorMessage = 'Это поле обязательно для заполнения';
        }
        
        // Проверка email
        if (isValid && validation.email && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Введите корректный email адрес';
            }
        }
        
        // Проверка URL
        if (isValid && validation.url && value) {
            try {
                new URL(value);
            } catch {
                isValid = false;
                errorMessage = 'Введите корректный URL';
            }
        }
        
        // Проверка минимальной длины
        if (isValid && validation.minLength && value.length < validation.minLength) {
            isValid = false;
            errorMessage = `Минимальная длина: ${validation.minLength} символов`;
        }
        
        // Проверка максимальной длины
        if (isValid && validation.maxLength && value.length > validation.maxLength) {
            isValid = false;
            errorMessage = `Максимальная длина: ${validation.maxLength} символов`;
        }
        
        // Проверка по паттерну
        if (isValid && validation.pattern && value) {
            const regex = new RegExp(validation.pattern);
            if (!regex.test(value)) {
                isValid = false;
                errorMessage = 'Неверный формат данных';
            }
        }
        
        if (isValid) {
            this.clearFieldError(field);
        } else {
            this.showFieldError(field, errorMessage);
        }
        
        return isValid;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('error');
        
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        
        field.parentNode.insertBefore(errorElement, field.nextSibling);
    }

    clearFieldError(field) {
        field.classList.remove('error');
        
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
    }

    setupFormValidation(form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit(form);
        });
    }

    async handleFormSubmit(form) {
        const formData = this.forms.get(form.id);
        if (!formData) return;
        
        // Валидация всех полей
        let isFormValid = true;
        const fields = Array.from(formData.fields.values());
        
        for (const fieldData of fields) {
            const isValid = this.validateField(form, fieldData.element);
            if (!isValid) {
                isFormValid = false;
            }
        }
        
        if (!isFormValid) {
            this.showFormError(form, 'Пожалуйста, исправьте ошибки в форме');
            return;
        }
        
        // Сбор данных формы
        const formDataObj = new FormData(form);
        const data = {};
        
        for (const [key, value] of formDataObj.entries()) {
            data[key] = value;
        }
        
        // Вызов обработчика отправки
        if (formData.submitHandler) {
            try {
                await formData.submitHandler(data, form);
            } catch (error) {
                console.error('Form submit error:', error);
                this.showFormError(form, 'Ошибка при отправке формы');
            }
        } else {
            // Стандартная отправка
            this.submitForm(form, data);
        }
    }

    async submitForm(form, data) {
        const formAction = form.action || window.location.href;
        const formMethod = form.method || 'POST';
        
        try {
            const response = await fetch(formAction, {
                method: formMethod,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showFormSuccess(form, result.message || 'Форма успешно отправлена');
            } else {
                this.showFormError(form, result.error || 'Ошибка при отправке формы');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            this.showFormError(form, 'Ошибка при отправке формы');
        }
    }

    showFormError(form, message) {
        this.clearFormMessages(form);
        
        const errorElement = document.createElement('div');
        errorElement.className = 'form-error';
        errorElement.textContent = message;
        
        form.insertBefore(errorElement, form.firstChild);
    }

    showFormSuccess(form, message) {
        this.clearFormMessages(form);
        
        const successElement = document.createElement('div');
        successElement.className = 'form-success';
        successElement.textContent = message;
        
        form.insertBefore(successElement, form.firstChild);
    }

    clearFormMessages(form) {
        const messages = form.querySelectorAll('.form-error, .form-success');
        messages.forEach(message => message.remove());
    }

    setSubmitHandler(formId, handler) {
        const formData = this.forms.get(formId);
        if (formData) {
            formData.submitHandler = handler;
        }
    }

    getFormData(formId) {
        const formData = this.forms.get(formId);
        if (!formData) return {};
        
        const data = {};
        for (const [name, fieldData] of formData.fields) {
            data[name] = fieldData.value;
        }
        
        return data;
    }

    setFormData(formId, data) {
        const formData = this.forms.get(formId);
        if (!formData) return;
        
        for (const [name, value] of Object.entries(data)) {
            const fieldData = formData.fields.get(name);
            if (fieldData) {
                fieldData.element.value = value;
                fieldData.value = value;
            }
        }
    }

    resetForm(formId) {
        const formData = this.forms.get(formId);
        if (!formData) return;
        
        formData.element.reset();
        
        for (const [name, fieldData] of formData.fields) {
            fieldData.value = '';
            this.clearFieldError(fieldData.element);
        }
        
        this.clearFormMessages(formData.element);
    }

    validateForm(formId) {
        const formData = this.forms.get(formId);
        if (!formData) return false;
        
        let isFormValid = true;
        const fields = Array.from(formData.fields.values());
        
        for (const fieldData of fields) {
            const isValid = this.validateField(formData.element, fieldData.element);
            if (!isValid) {
                isFormValid = false;
            }
        }
        
        return isFormValid;
    }
}

// Утилиты для работы с формами
class FormUtils {
    static serializeForm(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    }

    static populateForm(form, data) {
        for (const [name, value] of Object.entries(data)) {
            const field = form.querySelector(`[name="${name}"]`);
            if (field) {
                field.value = value;
            }
        }
    }

    static clearForm(form) {
        form.reset();
        const errorElements = form.querySelectorAll('.field-error, .form-error, .form-success');
        errorElements.forEach(element => element.remove());
    }

    static showFieldError(field, message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        
        field.classList.add('error');
        field.parentNode.insertBefore(errorElement, field.nextSibling);
    }

    static clearFieldError(field) {
        field.classList.remove('error');
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
    }
}

// Инициализация менеджера форм
let formManager;
document.addEventListener('DOMContentLoaded', () => {
    formManager = new FormManager();
});

// Экспорт для глобального доступа
window.formManager = formManager;
window.FormUtils = FormUtils;
