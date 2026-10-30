using System;
using System.Windows.Forms;

namespace Практика_9
{
    // Окно диалога «Добавить»: ввод новой записи с проверкой полей.
    public partial class DialogAdd : Form
    {
        public DialogAdd()
        {
            InitializeComponent();
        }

        private void DialogAdd_Load(object sender, EventArgs e)
        {
            dateTimePicker1.MaxDate = DateTime.Today;
            dateTimePicker1.Value = DateTime.Today.AddYears(-25);
        }

        private void buttonOK_Click(object sender, EventArgs e)
        {
            double money;
            string error = Record.CheckFields(textBox1.Text, textBox2.Text, textBox3.Text,
                listBox1.SelectedItem, dateTimePicker1.Value.Date, out money);

            if (error == null)       // Поля формы заполнены верно.
            {
                Record Tmp = new Record(textBox1.Text.Trim(), dateTimePicker1.Value.Date,
                    textBox2.Text.Trim(), listBox1.SelectedItem.ToString(), money);
                Form1.Rec = Tmp;     // Передаётся основной форме.
                DialogResult = DialogResult.OK;
                this.Close();
                return;
            }

            // OK — закрыть сообщение и исправить поля, Отмена — закрыть окно без добавления.
            var result = MessageBox.Show(error + "\n\nOK — вернуться к вводу,\nОтмена — закрыть окно без добавления.",
                "Проверка", MessageBoxButtons.OKCancel, MessageBoxIcon.Information);
            if (result == DialogResult.Cancel)
            {
                DialogResult = DialogResult.Cancel;
                this.Close();
            }
        }

        private void buttonCancel_Click(object sender, EventArgs e)
        {
            DialogResult = DialogResult.Cancel;
            this.Close();
        }
    }
}
