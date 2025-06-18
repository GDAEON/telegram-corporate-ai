import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import ru from './locales/ru.json';

const resources = {
  en: { translation: en },
  ru: { translation: ru },
};

const browserLang = navigator.language.split('-')[0];

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: browserLang in resources ? browserLang : 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
