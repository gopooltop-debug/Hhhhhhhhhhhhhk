using System;
using System.Windows.Forms;

namespace Практика_9
{
    // Окно диалога «Изменить»: в полях показана текущая запись, полученная с основной формы.
    public partial class Change : Form
    {
        public Change()
        {
            InitializeComponent();
        }

        private void Change_Load(object sender, EventArgs e)
        {
            dateTimePicker1.MaxDate = DateTime.Today;

            // Показать, что получено из главной формы.
            textBox1.Text = Form1.Rec.Name;
            textBox2.Text = Form1.Rec.Profession;
            if (Form1.Rec.BirthDate >= dateTimePicker1.MinDate && Form1.Rec.BirthDate <= dateTimePicker1.MaxDate)
                dateTimePicker1.Value = Form1.Rec.BirthDate;
            textBox3.Text = Form1.Rec.Money.ToString("0.##");

            // Отдел из файла может отсутствовать в списке — тогда добавим его.
            if (!listBox1.Items.Contains(Form1.Rec.Department) && Form1.Rec.Department != "")
                listBox1.Items.Add(Form1.Rec.Department);
            listBox1.SelectedItem = Form1.Rec.Department;
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
                Form1.Rec = Tmp;     // Изменённая запись передаётся основной форме.
                DialogResult = DialogResult.OK;
                this.Close();
                return;
            }

            // OK — закрыть сообщение и исправить поля, Отмена — закрыть окно без изменений.
            var result = MessageBox.Show(error + "\n\nOK — вернуться к вводу,\nОтмена — закрыть окно без изменений.",
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
