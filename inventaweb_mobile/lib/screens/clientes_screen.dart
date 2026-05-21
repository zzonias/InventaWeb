import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class ClientesScreen extends StatelessWidget {
  const ClientesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Clientes'),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: 4,
        itemBuilder: (context, index) {
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              contentPadding: const EdgeInsets.all(12),
              leading: CircleAvatar(
                backgroundColor: AppTheme.primaryColor.withValues(alpha: 0.2),
                child: const Icon(Icons.person, color: AppTheme.primaryColor),
              ),
              title: Text(
                'Cliente Mockado ${index + 1}',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text('cliente@email.com'),
                  Text('CPF: 000.000.000-00 | Tel: (11) 99999-9999', style: TextStyle(fontSize: 12, color: Colors.black54)),
                  SizedBox(height: 4),
                  Text(
                    'Compra frequente: Camiseta Básica', // Nova funcionalidade!
                    style: TextStyle(fontSize: 12, color: AppTheme.secondaryColor, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              isThreeLine: true,
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.person_add, color: Colors.white),
        onPressed: () {
          // Futura tela de adicionar cliente
        },
      ),
    );
  }
}
