import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import Management from "./management";
import Work from "./work";
import {BrowserRouter, Route, Routes} from "react-router";
import {LanguageProvider} from "./LanguageContext.tsx";

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <LanguageProvider><BrowserRouter>
            <Routes>
                <Route path="/" element={<App />} />
                <Route path="/work" element={<Work />} />
                <Route path="/manage" element={<Management />} />
            </Routes>
        </BrowserRouter></LanguageProvider>
    </StrictMode>,
)
