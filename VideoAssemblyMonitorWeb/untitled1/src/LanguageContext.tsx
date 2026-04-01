import React, { createContext, useContext, useState, ReactNode } from "react";
import {
    TextInterface,
    ChineseText,
    EnglishText,
    JapaneseText,
    FrenchText,
    GermanText,
    RussianText,
    KoreanText,
    ArabicText, TraditionalChineseText
} from "./language.ts";

interface LanguageContextProps {
    language: TextInterface;
    currentLangKey: string;
    changeLanguage: (langKey: string) => void;
}

const defaultContextValue: LanguageContextProps = {
    language: ChineseText,
    currentLangKey: "en",
    changeLanguage: () => {},
};

const LanguageContext = createContext<LanguageContextProps>(defaultContextValue);

export const useLanguage = (): LanguageContextProps => {
    return useContext(LanguageContext);
};

interface LanguageProviderProps {
    children: ReactNode;
}

export const LanguageProvider: React.FC<LanguageProviderProps> = ({ children }) => {
    const [langKey, setLangKey] = useState<string>("en");

    // 定义语言映射对象
    const languages: { [key: string]: TextInterface } = {
        zh: ChineseText,
        zh_tr: TraditionalChineseText,
        en: EnglishText,
        ja: JapaneseText,
        fr: FrenchText,
        de: GermanText,
        ru: RussianText,
        ko: KoreanText,
        ar: ArabicText,
    };

    // 根据当前 langKey 返回对应的语言文案，默认使用中文
    const language = languages[langKey] || ChineseText;

    const changeLanguage = (newLangKey: string) => {
        setLangKey(newLangKey);
    };

    return (
        <LanguageContext.Provider
            value={{
                language,
                currentLangKey: langKey,
                changeLanguage,
            }}
        >
            {children}
        </LanguageContext.Provider>
    );
};
