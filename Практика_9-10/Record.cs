using System;
using System.Globalization;

namespace Практика_9
{
    // Запись таблицы: данные об одном сотруднике.
    // Имя, дата рождения, должность, отдел, оклад.
    public class Record
    {
        // Разделитель полей записи в текстовом файле.
        public const char Separator = '#';

        // Формат даты в файле не зависит от настроек Windows.
        const string DateFormat = "dd.MM.yyyy";

        public string Name { get; set; }
        public DateTime BirthDate { get; set; }
        public string Profession { get; set; }
        public string Department { get; set; }
        public double Money { get; set; }

        // Конструктор по умолчанию.
        public Record()
        {
            Name = "";
            BirthDate = DateTime.Today;
            Profession = "";
            Department = "";
            Money = 0;
        }

        // Конструктор с параметрами.
        public Record(string name, DateTime birthDate, string profession, string department, double money)
        {
            Name = name;
            BirthDate = birthDate;
            Profession = profession;
            Department = department;
            Money = money;
        }

        // Конструктор копирования.
        public Record(Record other)
            : this(other.Name, other.BirthDate, other.Profession, other.Department, other.Money)
        {
        }

        // Строка для показа пользователю.
        public override string ToString()
        {
            return string.Format("{0}, {1:dd.MM.yyyy} г. р., {2}, отдел «{3}», оклад {4:N2} руб.",
                Name, BirthDate, Profession, Department, Money);
        }

        // Строка для записи в файл: поля через разделитель #.
        public string ToFileString()
        {
            return string.Join(Separator.ToString(),
                Name,
                BirthDate.ToString(DateFormat, CultureInfo.InvariantCulture),
                Profession,
                Department,
                Money.ToString(CultureInfo.InvariantCulture));
        }

        // Разбор строки файла в запись. При ошибке формата бросает FormatException.
        public static Record Parse(string record)
        {
            string[] fields = record.Split(Separator);
            if (fields.Length != 5)
                throw new FormatException("Ожидалось 5 полей, получено " + fields.Length);

            DateTime birthDate;
            if (!DateTime.TryParseExact(fields[1].Trim(), DateFormat, CultureInfo.InvariantCulture,
                    DateTimeStyles.None, out birthDate))
                throw new FormatException("Неверная дата: " + fields[1]);

            double money;
            if (!TryParseMoney(fields[4], out money))
                throw new FormatException("Неверный оклад: " + fields[4]);

            Record Tmp = new Record(fields[0].Trim(), birthDate, fields[2].Trim(), fields[3].Trim(), money);
            return Tmp;
        }

        // Оклад можно вводить и через точку, и через запятую, с пробелами между разрядами.
        public static bool TryParseMoney(string text, out double money)
        {
            string s = (text ?? "").Replace(" ", "").Replace(" ", "").Replace(',', '.');
            return double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out money);
        }

        // Проверка полей окна диалога. Возвращает текст ошибки или null, если всё верно.
        public static string CheckFields(string name, string profession, string moneyText,
            object department, DateTime birthDate, out double money)
        {
            money = 0;
            string empty = "";
            if (String.IsNullOrWhiteSpace(name)) empty += "\n  • Имя";
            if (String.IsNullOrWhiteSpace(profession)) empty += "\n  • Должность";
            if (String.IsNullOrWhiteSpace(moneyText)) empty += "\n  • Оклад";
            if (department == null) empty += "\n  • Отдел (выберите из списка)";
            if (empty != "")
                return "Не заполнены поля:" + empty;

            if ((name + profession).IndexOf(Separator) >= 0)
                return "Символ «" + Separator + "» нельзя использовать в тексте: он разделяет поля в файле.";
            if (!TryParseMoney(moneyText, out money))
                return "Оклад должен быть числом, например 45000 или 45000,50.";
            if (money < 0)
                return "Оклад не может быть отрицательным.";
            if (birthDate > DateTime.Today.AddYears(-14))
                return "Сотруднику должно быть не меньше 14 лет. Проверьте дату рождения.";
            return null;
        }
    }
}
