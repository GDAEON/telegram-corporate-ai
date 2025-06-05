import {
    RouterProvider,
  } from 'react-router-dom';
import {router} from './router';
import { ConfigProvider } from 'antd';

export const App = () => {
  return (
    <ConfigProvider
      theme={{
        token:{
          fontFamily: "'Nunito', sans-serif",
        }
      }}
      >
      <RouterProvider router={router}/>;
    </ConfigProvider>
  )
};