import {createBrowserRouter} from 'react-router-dom';
import { E_ROUTES } from '../shared';
import { ConnectionPage } from '../pages';


export const router = createBrowserRouter([
    {
        path: E_ROUTES.CONNECTION,
        element: <ConnectionPage/>,
    }
]);