import React from 'react';
import { getBaseApiUrl } from '../../config/api';

interface DiagnosticProps {
  etfs: any[];
  loading: boolean;
  error: any;
}

const ETFListDiagnostic: React.FC<DiagnosticProps> = ({ etfs, loading, error }) => {
  return (
    <div className="fixed bottom-4 right-4 bg-white p-4 rounded-lg shadow-lg border max-w-sm">
      <h4 className="font-semibold text-sm mb-2">🔍 Diagnostic ETF List</h4>
      
      <div className="space-y-2 text-xs">
        <div>
          <span className="font-medium">État:</span>
          <span className={`ml-2 px-2 py-1 rounded ${
            loading ? 'bg-blue-100 text-blue-800' : 
            error ? 'bg-red-100 text-red-800' : 
            'bg-green-100 text-green-800'
          }`}>
            {loading ? 'Chargement...' : error ? 'Erreur' : 'OK'}
          </span>
        </div>
        
        <div>
          <span className="font-medium">ETFs chargés:</span>
          <span className="ml-2">{etfs?.length || 0}</span>
        </div>
        
        {error && (
          <div>
            <span className="font-medium">Erreur:</span>
            <div className="text-red-600 text-xs mt-1 max-h-20 overflow-y-auto">
              {error.message || JSON.stringify(error, null, 2)}
            </div>
          </div>
        )}
        
        {etfs && etfs.length > 0 && (
          <div>
            <span className="font-medium">Premier ETF:</span>
            <div className="text-gray-600 text-xs mt-1">
              {etfs[0]?.symbol || 'N/A'} - {etfs[0]?.name || 'N/A'}
            </div>
          </div>
        )}
        
        <div>
          <span className="font-medium">API Base URL:</span>
          <div className="text-gray-600 text-xs">
            {getBaseApiUrl()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ETFListDiagnostic;